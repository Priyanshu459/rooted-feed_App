package online.rooted_feed.chat

import android.os.Bundle
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import online.rooted_feed.R
import online.rooted_feed.api.ApiService
import online.rooted_feed.api.SocketManager
import online.rooted_feed.model.ChatMessage
import org.json.JSONObject
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ChatActivity : AppCompatActivity() {

    private lateinit var adapter: ChatAdapter
    private val messages = mutableListOf<ChatMessage>()
    private var targetHandle: String = "admin" // Default for testing
    private lateinit var recyclerView: RecyclerView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_chat)

        // Get target handle from intent
        targetHandle = intent.getStringExtra("TARGET_HANDLE") ?: "admin"
        val targetName = intent.getStringExtra("TARGET_NAME") ?: "Rooted Admin"
        val targetPhoto = intent.getStringExtra("TARGET_PHOTO") ?: ""

        // Initialize Views
        recyclerView = findViewById(R.id.chatRecyclerView)
        val messageInput: EditText = findViewById(R.id.messageInput)
        val sendButton: ImageButton = findViewById(R.id.sendButton)
        val toolbarTitle: TextView = findViewById(R.id.toolbarTitle)
        val toolbarAvatar: ImageView = findViewById(R.id.toolbarAvatar)

        toolbarTitle.text = targetName
        if (targetPhoto.isNotEmpty()) {
            Glide.with(this).load(targetPhoto).into(toolbarAvatar)
        }

        adapter = ChatAdapter(messages)
        recyclerView.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        recyclerView.adapter = adapter

        // 1. Connect Socket
        SocketManager.getSocket()?.on("receive_message") { args ->
            runOnUiThread {
                val data = args[0] as JSONObject
                val content = data.getString("text")
                val sender = data.getString("sender_handle")
                
                val msg = ChatMessage(
                    content = content,
                    senderHandle = sender,
                    isMe = sender != targetHandle // This logic depends on current user handle
                )
                messages.add(msg)
                adapter.notifyItemInserted(messages.size - 1)
                recyclerView.scrollToPosition(messages.size - 1)
            }
        }
        SocketManager.connect()

        // 2. Load History via Retrofit
        loadChatHistory()

        sendButton.setOnClickListener {
            val text = messageInput.text.toString()
            if (text.isNotEmpty()) {
                SocketManager.sendMessage(targetHandle, text)
                messageInput.text.clear()
            }
        }
    }

    private fun loadChatHistory() {
        val retrofit = Retrofit.Builder()
            .baseUrl("https://www.rooted-feed.online")
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        val api = retrofit.create(ApiService::class.java)
        api.getMessages(targetHandle).enqueue(object : Callback<List<ChatMessage>> {
            override fun onResponse(call: Call<List<ChatMessage>>, response: Response<List<ChatMessage>>) {
                if (response.isSuccessful) {
                    response.body()?.let {
                        messages.clear()
                        messages.addAll(it)
                        adapter.notifyDataSetChanged()
                        recyclerView.scrollToPosition(messages.size - 1)
                    }
                }
            }

            override fun onFailure(call: Call<List<ChatMessage>>, t: Throwable) {
                // Handle error
            }
        })
    }

    override fun onDestroy() {
        super.onDestroy()
        SocketManager.getSocket()?.off("receive_message")
    }
}
