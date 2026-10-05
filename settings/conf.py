from pathlib import Path

from decouple import Config, RepositoryEnv

ENV_FILE = Path(__file__).parent / '.env'

config = Config(RepositoryEnv(str(ENV_FILE)))


SECRET_KEY = config('BLOG_SECRET_KEY')


