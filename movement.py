def Player_input():
    key = input("Enter a key: ")
    if key == 'w':
        print("player moved up")
        return 'up'
    elif key == 'a':
        print("player moved left")
        return 'left'
    elif key == 's':
        print("player moved down")
        return 'down'
    elif key == 'd':
        print("player moved right")
        return 'right'
while 1 > 0:
    Player_input()
