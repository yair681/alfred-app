package com.alfred.app

import retrofit2.http.Body
import retrofit2.http.POST

data class ChatRequest(val message: String, val user_id: String = "alfred_user")
data class ChatResponse(val reply: String)

interface ApiService {
    @POST("chat")
    suspend fun sendMessage(@Body request: ChatRequest): ChatResponse
}
