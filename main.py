import sys
from agent_postman.cli import main, interactive

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        interactive()
