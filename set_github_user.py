# Writes your GitHub user name into the Colab badge of README.md and into the clone address of colab_demo.ipynb.
# Usage: python set_github_user.py YOUR_GITHUB_USERNAME
import sys  # command line arguments

user = sys.argv[1]  # the GitHub user name
for path in ("README.md", "colab_demo.ipynb"):  # the two files that hold the placeholder
    text = open(path, encoding="utf-8").read()  # read the file
    open(path, "w", encoding="utf-8").write(text.replace("YOUR_GITHUB_USERNAME", user))  # replace the placeholder
    print("updated", path)  # report
