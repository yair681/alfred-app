package com.alfred.app

import android.view.Gravity
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.LinearLayout
import androidx.recyclerview.widget.RecyclerView
import com.alfred.app.databinding.ItemMessageBinding

class ChatAdapter(private val messages: List<Message>) :
    RecyclerView.Adapter<ChatAdapter.MessageViewHolder>() {

    inner class MessageViewHolder(private val binding: ItemMessageBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(message: Message) {
            binding.tvMessage.text = message.text
            if (message.isUser) {
                binding.tvMessage.setBackgroundResource(R.drawable.bubble_user)
                (binding.tvMessage.layoutParams as LinearLayout.LayoutParams).gravity = Gravity.END
                binding.messageContainer.gravity = Gravity.END
            } else {
                binding.tvMessage.setBackgroundResource(R.drawable.bubble_alfred)
                (binding.tvMessage.layoutParams as LinearLayout.LayoutParams).gravity = Gravity.START
                binding.messageContainer.gravity = Gravity.START
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MessageViewHolder {
        val binding = ItemMessageBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return MessageViewHolder(binding)
    }

    override fun onBindViewHolder(holder: MessageViewHolder, position: Int) {
        holder.bind(messages[position])
    }

    override fun getItemCount() = messages.size
}
