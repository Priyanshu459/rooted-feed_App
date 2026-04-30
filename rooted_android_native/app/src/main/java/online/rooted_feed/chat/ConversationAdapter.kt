package online.rooted_feed.chat

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import online.rooted_feed.R
import online.rooted_feed.model.Conversation

class ConversationAdapter(
    private val conversations: List<Conversation>,
    private val onClick: (Conversation) -> Unit
) : RecyclerView.Adapter<ConversationAdapter.ConvViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ConvViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_conversation, parent, false)
        return ConvViewHolder(view)
    }

    override fun onBindViewHolder(holder: ConvViewHolder, position: Int) {
        val conv = conversations[position]
        holder.bind(conv)
        holder.itemView.setOnClickListener { onClick(conv) }
    }

    override fun getItemCount(): Int = conversations.size

    class ConvViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        private val avatar: ImageView = view.findViewById(R.id.convAvatar)
        private val name: TextView = view.findViewById(R.id.convName)
        private val lastMessage: TextView = view.findViewById(R.id.convLastMessage)

        fun bind(conv: Conversation) {
            name.text = conv.other_user_name
            lastMessage.text = conv.last_message
            if (conv.other_user_photo.isNotEmpty()) {
                Glide.with(itemView.context)
                    .load(conv.other_user_photo)
                    .placeholder(R.drawable.splash_background)
                    .into(avatar)
            }
        }
    }
}
