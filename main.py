from fastapi import FastAPI
import routers

app = FastAPI()


@app.get("/", tags=['Home'])
async def home():
    return {'message': 'Welcome to the German-Context App!'}


app.include_router(routers.users)
app.include_router(routers.words)
app.include_router(routers.admin_users)
app.include_router(routers.admin_user_words)
app.include_router(routers.admin_words)
app.include_router(routers.security)

# todo user roles
# todo user activation mail
# todo topics endpoints
# todo search words by syllables endpoint
# todo show cards logic
# todo words pagination
# todo pep8
# todo conjugations, declensions (nouns, pronouns, adjectives, articles, verbs)

# mvp
# todo deployment (render/vps)

# v2
# todo unit testing
# todo security and validation (pydantic, bleach)
# todo react frontend
