package com.alfred.app

import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.os.IBinder
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.view.inputmethod.EditorInfo
import android.widget.EditText
import android.widget.ImageButton
import android.widget.TextView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.URL
import javax.net.ssl.HttpsURLConnection

class FloatingButtonService : Service() {

    private lateinit var windowManager: WindowManager
    private var fabView: View? = null
    private var chatView: View? = null
    private var fabParams: WindowManager.LayoutParams? = null
    private val scope = CoroutineScope(Dispatchers.Main)

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        showFab()
    }

    private fun showFab() {
        val view = LayoutInflater.from(this).inflate(R.layout.floating_button, null)
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).also {
            it.gravity = Gravity.TOP or Gravity.START
            it.x = 0
            it.y = 300
        }
        fabParams = params

        var startX = 0f; var startY = 0f; var moved = false
        view.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = event.rawX - params.x
                    startY = event.rawY - params.y
                    moved = false
                }
                MotionEvent.ACTION_MOVE -> {
                    val nx = (event.rawX - startX).toInt()
                    val ny = (event.rawY - startY).toInt()
                    if (Math.abs(nx - params.x) > 8 || Math.abs(ny - params.y) > 8) moved = true
                    params.x = nx; params.y = ny
                    windowManager.updateViewLayout(view, params)
                }
                MotionEvent.ACTION_UP -> if (!moved) openChat()
            }
            true
        }

        fabView = view
        windowManager.addView(view, params)
    }

    private fun openChat() {
        fabView?.visibility = View.GONE

        if (chatView != null) {
            chatView?.visibility = View.VISIBLE
            return
        }

        val view = LayoutInflater.from(this).inflate(R.layout.floating_chat, null)
        val params = WindowManager.LayoutParams(
            (280 * resources.displayMetrics.density).toInt(),
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).also {
            it.gravity = Gravity.TOP or Gravity.START
            it.x = 20
            it.y = fabParams?.y ?: 300
        }

        val tvResponse = view.findViewById<TextView>(R.id.tvResponse)
        val etInput = view.findViewById<EditText>(R.id.etFloatInput)
        val btnSend = view.findViewById<ImageButton>(R.id.btnFloatSend)

        view.findViewById<ImageButton>(R.id.btnClose).setOnClickListener {
            view.visibility = View.GONE
            fabView?.visibility = View.VISIBLE
        }

        view.findViewById<ImageButton>(R.id.btnExpand).setOnClickListener {
            startActivity(Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            })
        }

        fun send() {
            val text = etInput.text.toString().trim()
            if (text.isEmpty()) return
            etInput.setText("")
            tvResponse.text = "..."
            btnSend.isEnabled = false
            scope.launch {
                val reply = withContext(Dispatchers.IO) {
                    try {
                        val url = URL("${RetrofitClient.BASE_URL}chat")
                        val conn = url.openConnection() as HttpsURLConnection
                        conn.requestMethod = "POST"
                        conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                        conn.doOutput = true
                        conn.connectTimeout = 60000
                        conn.readTimeout = 60000
                        val body = """{"user_id":"alfred_user","message":"${text.replace("\"", "'")}"}"""
                        conn.outputStream.write(body.toByteArray(Charsets.UTF_8))
                        val response = conn.inputStream.bufferedReader(Charsets.UTF_8).readText()
                        JSONObject(response).getString("reply")
                    } catch (e: Exception) { "שגיאה: ${e.message}" }
                }
                tvResponse.text = reply
                btnSend.isEnabled = true
            }
        }

        btnSend.setOnClickListener { send() }
        etInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEND) { send(); true } else false
        }

        chatView = view
        windowManager.addView(view, params)
    }

    override fun onDestroy() {
        super.onDestroy()
        fabView?.let { runCatching { windowManager.removeView(it) } }
        chatView?.let { runCatching { windowManager.removeView(it) } }
    }
}
