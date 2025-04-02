from fastapi import FastAPI
import routers

app = FastAPI(title='Brain Germination App',
              description="The app aims to help users study some German showing user's words in different contexts.")

app.include_router(routers.home_routes)
app.include_router(routers.users)
app.include_router(routers.words)
app.include_router(routers.user_topics)
app.include_router(routers.cards)
app.include_router(routers.admin_users)
app.include_router(routers.admin_user_words)
app.include_router(routers.admin_user_topics)
app.include_router(routers.admin_words)
app.include_router(routers.admin_topics)
app.include_router(routers.security)

# todo docstrings

# v2
# todo unit testing
# todo adjust server time
# todo genai endpoints
# todo filters
# todo user activation mail (background tasks)
# todo security and validation (pydantic, bleach)
# todo react frontend
# todo conjugations, declensions (nouns, pronouns, adjectives, articles, verbs)
