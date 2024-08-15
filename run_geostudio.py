import sys
import os

# # Determine if we're running from the executable or not
# if getattr(sys, 'frozen', False):
#     # If we're running from the exe, use this path
#     application_path = os.path.dirname(sys.executable)
# else:
#     # If we're running from a script, use this path
#     application_path = os.path.dirname(os.path.abspath(__file__))
#
# # Add the application path to sys.path
# sys.path.insert(0, application_path)
#
# # Set the working directory to the application path
# os.chdir(application_path)

from main.main import example_geostudio

if __name__ == "__main__":
    example_geostudio()