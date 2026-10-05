#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from decouple import Config, RepositoryEnv


def main():
   env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'settings','.env'
                           )
   env_config = Config(RepositoryEnv(env_path))
   env_id =  env_config("BLOG_ENV_ID" , default="local")

   os.environ.setdefault(
       "DJANGO_SETTINGS_MODULE",
       f"settings.env.{env_id}")

   from django.core.management import execute_from_command_line
   execute_from_command_line(sys.argv)



if __name__ == '__main__':
    main()
