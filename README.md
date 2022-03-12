## Snake Game (pygame)
Variation of the game "Snake" - players grow by eating food. The main task is to grow as much as possible, and prevent your opponents from doing it. This game has some minor features:
- the player dies when his head touches an obstacle;
- the main character has an acceleration on the ↑ button, the rotation is carried out using the ← and → buttons;
- bots can dodge obstacles a little;
- bots do not end.

## GUI
![alt text](https://github.com/bulatto/snake_game/blob/master/SnakeGame.gif "Snake GUI")

### Installation and running
    sudo apt install git python3-venv
    git clone https://github.com/bulatto/snake_game.git
    cd snake_game
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python3 snake

