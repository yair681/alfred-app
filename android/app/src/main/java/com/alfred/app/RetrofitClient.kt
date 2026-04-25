package com.alfred.app

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    // Change this to your Render URL after deployment
    // For local testing: http://10.0.2.2:8000/ (Android emulator)
    private const val BASE_URL = "https://alfred-server-6mlw.onrender.com/"

    val api: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
