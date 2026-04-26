package com.alfred.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.URL
import java.util.concurrent.TimeUnit

class ReminderWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            val url = URL("${RetrofitClient.BASE_URL}notifications/alfred_user")
            val response = url.readText()
            val json = JSONObject(response)
            val notifications = json.getJSONArray("notifications")

            if (notifications.length() > 0) {
                val nm = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                ensureChannel(nm)
                for (i in 0 until notifications.length()) {
                    val msg = notifications.getString(i)
                    showNotification(nm, msg, i)
                }
            }
        } catch (_: Exception) {}

        scheduleNext(applicationContext)
        Result.success()
    }

    private fun ensureChannel(nm: NotificationManager) {
        val channel = NotificationChannel(CHANNEL_ID, "תזכורות אלפרד", NotificationManager.IMPORTANCE_HIGH)
        channel.description = "תזכורות מאלפרד"
        nm.createNotificationChannel(channel)
    }

    private fun showNotification(nm: NotificationManager, message: String, id: Int) {
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("🔔 אלפרד")
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()
        nm.notify(System.currentTimeMillis().toInt() + id, notification)
    }

    companion object {
        const val CHANNEL_ID = "alfred_reminders"

        fun scheduleNext(context: Context) {
            val request = OneTimeWorkRequestBuilder<ReminderWorker>()
                .setInitialDelay(1, TimeUnit.MINUTES)
                .build()
            WorkManager.getInstance(context).enqueueUniqueWork(
                "alfred_reminder_poll",
                ExistingWorkPolicy.REPLACE,
                request
            )
        }
    }
}
