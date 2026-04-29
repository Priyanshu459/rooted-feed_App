import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Flora

with app.app_context():
    # Step 1: find first user
    u = User.query.first()
    if not u:
        print("ERROR: No users in database!")
    else:
        print(f"User: {u.handle}, id={u.id}")
        
        # Step 2: Test mutual_followers endpoint logic
        followed = u.followed.all()
        followers_list = u.followers.all()
        mutuals = [x for x in followed if x in followers_list]
        print(f"Mutuals: {[x.handle for x in mutuals]}")
        
        # Step 3: Test flora creation
        ts = int(__import__('time').time() * 1000)
        try:
            flora = Flora(name='Test Flora', description='Test Desc', creator_id=u.id, created_at=ts)
            db.session.add(flora)
            db.session.flush()  # flush to get ID
            print(f"Flora id after flush: {flora.id}")
            flora.members.append(u)
            db.session.commit()
            print(f"Flora created! ID={flora.id}")
        except Exception as e:
            db.session.rollback()
            print(f"CREATION ERROR: {e}")
        
        # Step 4: Test get_my_floras
        try:
            floras = u.floras.order_by(Flora.created_at.desc()).all()
            print(f"Floras for {u.handle}: {[f.name for f in floras]}")
            for f in floras:
                mems = f.members.all()
                print(f"  Flora '{f.name}' members: {[m.handle for m in mems]}")
        except Exception as e:
            print(f"FETCH ERROR: {e}")
