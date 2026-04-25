package com.alfred.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Base64
import android.view.inputmethod.EditorInfo
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updatePadding
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.alfred.app.databinding.ActivityMainBinding
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.util.concurrent.TimeUnit

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
            view.updatePadding(bottom = systemBars.bottom)
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
        val workRequest = PeriodicWorkRequestBuilder<ReminderWorker>(1, TimeUnit.MINUTES)
            .build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "alfred_reminder_poll",
            androidx.work.ExistingPeriodicWorkPolicy.KEEP,
            workRequest
        )
    }

    private fun addMessage(text: String, isUser: Boolean) {
        messages.add(Message(text, isUser))
        adapter.notifyItemInserted(messages.size - 1)
        binding.rvChat.scrollToPosition(messages.size - 1)
    }
}
