package online.rooted_feed.chat

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import online.rooted_feed.R
import online.rooted_feed.api.ApiService
import online.rooted_feed.model.Conversation
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ConversationActivity : AppCompatActivity() {

    private lateinit var adapter: ConversationAdapter
    private val conversations = mutableListOf<Conversation>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_conversation)

        val recyclerView: RecyclerView = findViewById(R.id.convRecyclerView)
        recyclerView.layoutManager = LinearLayoutManager(this)
        
        adapter = ConversationAdapter(conversations) { conv ->
            val intent = Intent(this, ChatActivity::class.java).apply {
                putExtra("TARGET_HANDLE", conv.other_user_handle)
                putExtra("TARGET_NAME", conv.other_user_name)
                putExtra("TARGET_PHOTO", conv.other_user_photo)
            }
            startActivity(intent)
        }
        recyclerView.adapter = adapter

        loadConversations()
    }

    private fun loadConversations() {
        val retrofit = Retrofit.Builder()
            .baseUrl("https://www.rooted-feed.online")
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        val api = retrofit.create(ApiService::class.java)
        api.getConversations().enqueue(object : Callback<List<Conversation>> {
            override fun onResponse(call: Call<List<Conversation>>, response: Response<List<Conversation>>) {
                if (response.isSuccessful) {
                    response.body()?.let {
                        conversations.clear()
                        conversations.addAll(it)
                        adapter.notifyDataSetChanged()
                    }
                }
            }

            override fun onFailure(call: Call<List<Conversation>>, t: Throwable) {
                // Handle error
            }
        })
    }
}
