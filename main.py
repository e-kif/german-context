from fastapi import FastAPI
import routers

app = FastAPI(title='German Context App',
              description="The app aims to help users study some German showing user's words in different contexts.")


app.include_router(routers.home_routes)
app.include_router(routers.users)
app.include_router(routers.words)
app.include_router(routers.user_topics)
app.include_router(routers.admin_users)
app.include_router(routers.admin_user_words)
app.include_router(routers.admin_user_topics)
app.include_router(routers.admin_words)
app.include_router(routers.admin_topics)
app.include_router(routers.security)

# todo user activation mail
# todo show cards logic
# todo pep8
# todo conjugations, declensions (nouns, pronouns, adjectives, articles, verbs)

# mvp
# todo deployment (render/vps)

# v2
# todo unit testing
# todo genai endpoints
# todo filters, nouns sorting by word
# todo security and validation (pydantic, bleach)
# todo react frontend
