package com.alfred.app

import android.Manifest
import android.app.AlertDialog
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Base64
import android.view.inputmethod.EditorInfo
import android.widget.Switch
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updatePadding
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.work.WorkManager
import com.alfred.app.databinding.ActivityMainBinding
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val messages = mutableListOf<Message>()
    private lateinit var adapter: ChatAdapter
    private var pendingImageBase64: String? = null

    private val pickImage = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let {
            pendingImageBase64 = uriToBase64(it)
            binding.btnImage.setBackgroundColor(0xFF4CAF50.toInt())
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            val ime = insets.getInsets(WindowInsetsCompat.Type.ime())
            view.updatePadding(bottom = maxOf(systemBars.bottom, ime.bottom))
            insets
        }

        requestNotificationPermission()
        startReminderPolling()

        adapter = ChatAdapter(messages)
        binding.rvChat.layoutManager = LinearLayoutManager(this).also { it.stackFromEnd = true }
        binding.rvChat.adapter = adapter

        binding.btnSend.setOnClickListener { sendMessage() }
        binding.btnImage.setOnClickListener { pickImage.launch("image/*") }
        binding.etInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEND) { sendMessage(); true } else false
        }
        binding.btnSettings.setOnClickListener { showSettingsDialog() }

        addMessage("היי! אלפרד לשירותך — מוכן לעזור, לבלבל, ולהצחיק בסדר הזה בדיוק 😄", isUser = false)
    }

    private fun sendMessage() {
        val text = binding.etInput.text.toString().trim()
        val image = pendingImageBase64
        if (text.isEmpty() && image == null) return

        binding.etInput.setText("")
        pendingImageBase64 = null
        binding.btnImage.setBackgroundColor(0xFFE0E0E0.toInt())

        val displayText = if (image != null && text.isEmpty()) "📷 תמונה" else if (image != null) "📷 $text" else text
        addMessage(displayText, isUser = true)
        binding.btnSend.isEnabled = false

        lifecycleScope.launch {
            try {
                val response = RetrofitClient.api.sendMessage(
                    ChatRequest(message = text, image_base64 = image)
                )
                addMessage(response.reply, isUser = false)
            } catch (e: Exception) {
                val errorMsg = "שגיאה: ${e.javaClass.simpleName} — ${e.message ?: "unknown"}"
                addMessage(errorMsg, isUser = false)
                android.util.Log.e("Alfred", "Chat error", e)
            } finally {
                binding.btnSend.isEnabled = true
            }
        }
    }

    private fun uriToBase64(uri: Uri): String {
        val inputStream = contentResolver.openInputStream(uri) ?: return ""
        val bitmap = BitmapFactory.decodeStream(inputStream)
        val output = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, output)
        return Base64.encodeToString(output.toByteArray(), Base64.NO_WRAP)
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
            }
        }
    }

    private fun startReminderPolling() {
        ReminderWorker.scheduleNext(this)
    }

    private fun showSettingsDialog() {
        val prefs = getSharedPreferences("alfred_prefs", MODE_PRIVATE)
        val isEnabled = prefs.getBoolean("floating_button", false)

        @Suppress("DEPRECATION")
        val toggle = Switch(this).apply {
            text = "כפתור צף"
            isChecked = isEnabled
            setPadding(32, 32, 32, 32)
        }

        AlertDialog.Builder(this)
            .setTitle("הגדרות")
            .setView(toggle)
            .setPositiveButton("שמור") { _, _ ->
                val enabled = toggle.isChecked
                prefs.edit().putBoolean("floating_button", enabled).apply()
                if (enabled) enableFloatingButton() else disableFloatingButton()
            }
            .setNegativeButton("ביטול", null)
            .show()
    }

    private fun enableFloatingButton() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
        } else {
            startService(Intent(this, FloatingButtonService::class.java))
        }
    }

    private fun disableFloatingButton() {
        stopService(Intent(this, FloatingButtonService::class.java))
    }

    override fun onResume() {
        super.onResume()
        val prefs = getSharedPreferences("alfred_prefs", MODE_PRIVATE)
        if (prefs.getBoolean("floating_button", false) &&
            (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Settings.canDrawOverlays(this))) {
            startService(Intent(this, FloatingButtonService::class.java))
        }
    }

    private fun addMessage(text: String, isUser: Boolean) {
        messages.add(Message(text, isUser))
        adapter.notifyItemInserted(messages.size - 1)
        binding.rvChat.scrollToPosition(messages.size - 1)
    }
}
