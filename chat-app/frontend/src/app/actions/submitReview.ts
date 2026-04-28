'use server'

import { createClient } from '@/utils/supabase/server'
import { revalidatePath } from 'next/cache'

export async function submitReviewAction(formData: any) {
  const supabase = createClient()

  // 1. Get the current logged-in user
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  
  if (authError || !user) {
    throw new Error('You must be logged in to leave a review.')
  }

  // 2. We would normally check if the landlord & property exist here, 
  // and create them if they don't. For simplicity, let's assume we have a property_id:
  const dummyPropertyId = "some-uuid-from-db"; 

  // 3. Insert the review
  const { error } = await supabase
    .from('reviews')
    .insert([
      {
        property_id: dummyPropertyId,
        user_id: user.id,
        rating_noise: formData.noise,
        rating_maintenance: formData.maintenance,
        rating_safety: formData.safety,
        rating_pests: formData.pests,
        written_review: formData.reviewText,
        is_verified: false 
      }
    ])

  if (error) {
    console.error("Database Error:", error)
    throw new Error('Failed to submit review.')
  }

  // Clear cache to show new review
  revalidatePath('/property/[id]')
  
  return { success: true }
}
