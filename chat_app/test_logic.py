import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Flora
with app.app_context():
    # Let's create two users and test the mutual followers and flora creation
    u1 = User(email="test1@test.com", handle="@test1", display_name="Test 1")
    u2 = User(email="test2@test.com", handle="@test2", display_name="Test 2")
    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()
    
    u1.follow(u2)
    u2.follow(u1)
    db.session.commit()
    
    # Simulate /api/mutual_followers
    followed = u1.followed.all()
    followers = u1.followers.all()
    mutuals = [u for u in followed if u in followers]
    print(f"Mutuals for test1: {[u.handle for u in mutuals]}")
    
    # Simulate create_flora
    flora = Flora(name="My Flora", description="Desc", creator_id=u1.id, created_at=123)
    db.session.add(flora)
    flora.members.append(u1)
    for u in mutuals:
        flora.members.append(u)
    db.session.commit()
    
    print(f"Flora members: {[u.handle for u in flora.members]}")
    
    # Simulate get_my_floras
    floras = u1.floras.order_by(Flora.created_at.desc()).all()
    print(f"Test1 Floras: {[f.name for f in floras]}")
