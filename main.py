from fastapi import FastAPI
import routers

app = FastAPI(title='German Context App',
              description="The app aims to help users study some German showing user's words in different contexts.")


@app.get("/", tags=['Home'])
async def home():
    return {'message': 'Welcome to the German-Context App!'}


app.include_router(routers.users)
app.include_router(routers.words)
app.include_router(routers.user_topics)
app.include_router(routers.admin_users)
app.include_router(routers.admin_user_words)
app.include_router(routers.admin_words)
app.include_router(routers.security)

# todo user activation mail
# todo topics endpoints
# todo search words by syllables endpoint
# todo show cards logic
# todo paginations
# todo pep8
# todo conjugations, declensions (nouns, pronouns, adjectives, articles, verbs)

# mvp
# todo deployment (render/vps)

# v2
# todo unit testing
# todo security and validation (pydantic, bleach)
# todo react frontend
