package com.alfred.app

import android.os.Bundle
import android.view.inputmethod.EditorInfo
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updatePadding
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.alfred.app.databinding.ActivityMainBinding
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val messages = mutableListOf<Message>()
    private lateinit var adapter: ChatAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.updatePadding(bottom = systemBars.bottom)
            insets
        }

        adapter = ChatAdapter(messages)
        binding.rvChat.layoutManager = LinearLayoutManager(this).also { it.stackFromEnd = true }
        binding.rvChat.adapter = adapter

        binding.btnSend.setOnClickListener { sendMessage() }
        binding.etInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEND) { sendMessage(); true } else false
        }

        addMessage("היי! אלפרד לשירותך — מוכן לעזור, לבלבל, ולהצחיק בסדר הזה בדיוק 😄", isUser = false)
    }

    private fun sendMessage() {
        val text = binding.etInput.text.toString().trim()
        if (text.isEmpty()) return
        binding.etInput.setText("")
        addMessage(text, isUser = true)
        binding.btnSend.isEnabled = false

        lifecycleScope.launch {
            try {
                val response = RetrofitClient.api.sendMessage(ChatRequest(text))
                addMessage(response.reply, isUser = false)
            } catch (e: Exception) {
                addMessage("סליחה, לא הצלחתי להתחבר לשרת 😅", isUser = false)
            } finally {
                binding.btnSend.isEnabled = true
            }
        }
    }

    private fun addMessage(text: String, isUser: Boolean) {
        messages.add(Message(text, isUser))
        adapter.notifyItemInserted(messages.size - 1)
        binding.rvChat.scrollToPosition(messages.size - 1)
    }
}
