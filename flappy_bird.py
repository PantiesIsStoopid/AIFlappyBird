"""
The classic game of flappy bird. Make with python
and pygame. Features pixel perfect collision using masks :o

Date Modified:  Jul 30, 2019
Author: Tech With Tim
Estimated Work Time: 5 hours (1 just for that damn collision)
"""
import pygame
import random
import os
import time
import neat
import visualize
import pickle
pygame.font.init()  # init font

WinWidth = 600
WinHeight = 800
Floor = 730
StatFont = pygame.font.SysFont("comicsans", 50)
EndFont = pygame.font.SysFont("comicsans", 70)
DrawLines = False

Win = pygame.display.set_mode((WinWidth, WinHeight))
pygame.display.set_caption("Flappy Bird")

PipeImg = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
BgImg = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
BirdImages = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
BaseImg = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

Gen = 0

class Bird:
    """
    Bird class representing the flappy bird
    """
    MaxRotation = 25
    Imgs = BirdImages
    RotVel = 20
    AnimationTime = 5

    def __init__(self, x, y):
        """
        Initialize the object
        :param x: starting x pos (int)
        :param y: starting y pos (int)
        :return: None
        """
        self.X = x
        self.Y = y
        self.Tilt = 0  # degrees to tilt
        self.TickCount = 0
        self.Vel = 0
        self.Height = self.Y
        self.ImgCount = 0
        self.Img = self.Imgs[0]

    def Jump(self):
        """
        make the bird jump
        :return: None
        """
        self.Vel = -10.5
        self.TickCount = 0
        self.Height = self.Y

    def Move(self):
        """
        make the bird move
        :return: None
        """
        self.TickCount += 1

        # for downward acceleration
        Displacement = self.Vel*(self.TickCount) + 0.5*(3)*(self.TickCount)**2  # calculate displacement

        # terminal velocity
        if Displacement >= 16:
            Displacement = (Displacement/abs(Displacement)) * 16

        if Displacement < 0:
            Displacement -= 2

        self.Y = self.Y + Displacement

        if Displacement < 0 or self.Y < self.Height + 50:  # tilt up
            if self.Tilt < self.MaxRotation:
                self.Tilt = self.MaxRotation
        else:  # tilt down
            if self.Tilt > -90:
                self.Tilt -= self.RotVel

    def Draw(self, Win):
        """
        draw the bird
        :param win: pygame window or surface
        :return: None
        """
        self.ImgCount += 1

        # For animation of bird, loop through three images
        if self.ImgCount <= self.AnimationTime:
            self.Img = self.Imgs[0]
        elif self.ImgCount <= self.AnimationTime*2:
            self.Img = self.Imgs[1]
        elif self.ImgCount <= self.AnimationTime*3:
            self.Img = self.Imgs[2]
        elif self.ImgCount <= self.AnimationTime*4:
            self.Img = self.Imgs[1]
        elif self.ImgCount == self.AnimationTime*4 + 1:
            self.Img = self.Imgs[0]
            self.ImgCount = 0

        # so when bird is nose diving it isn't flapping
        if self.Tilt <= -80:
            self.Img = self.Imgs[1]
            self.ImgCount = self.AnimationTime*2


        # tilt the bird
        BlitRotateCenter(Win, self.Img, (self.X, self.Y), self.Tilt)

    def GetMask(self):
        """
        gets the mask for the current image of the bird
        :return: None
        """
        return pygame.mask.from_surface(self.Img)


class Pipe():
    """
    represents a pipe object
    """
    Gap = 200
    Vel = 5

    def __init__(self, x):
        """
        initialize pipe object
        :param x: int
        :param y: int
        :return" None
        """
        self.X = x
        self.Height = 0

        # where the top and bottom of the pipe is
        self.Top = 0
        self.Bottom = 0

        self.PipeTop = pygame.transform.flip(PipeImg, False, True)
        self.PipeBottom = PipeImg

        self.Passed = False

        self.SetHeight()

    def SetHeight(self):
        """
        set the height of the pipe, from the top of the screen
        :return: None
        """
        self.Height = random.randrange(50, 450)
        self.Top = self.Height - self.PipeTop.get_height()
        self.Bottom = self.Height + self.Gap

    def Move(self):
        """
        move pipe based on vel
        :return: None
        """
        self.X -= self.Vel

    def Draw(self, Win):
        """
        draw both the top and bottom of the pipe
        :param win: pygame window/surface
        :return: None
        """
        # draw top
        Win.blit(self.PipeTop, (self.X, self.Top))
        # draw bottom
        Win.blit(self.PipeBottom, (self.X, self.Bottom))


    def Collide(self, Bird, Win):
        """
        returns if a point is colliding with the pipe
        :param bird: Bird object
        :return: Bool
        """
        BirdMask = Bird.GetMask()
        TopMask = pygame.mask.from_surface(self.PipeTop)
        BottomMask = pygame.mask.from_surface(self.PipeBottom)
        TopOffset = (self.X - Bird.X, self.Top - round(Bird.Y))
        BottomOffset = (self.X - Bird.X, self.Bottom - round(Bird.Y))

        BPoint = BirdMask.overlap(BottomMask, BottomOffset)
        TPoint = BirdMask.overlap(TopMask,TopOffset)

        if BPoint or TPoint:
            return True

        return False

class Base:
    """
    Represnts the moving floor of the game
    """
    Vel = 5
    Width = BaseImg.get_width()
    Img = BaseImg

    def __init__(self, y):
        """
        Initialize the object
        :param y: int
        :return: None
        """
        self.Y = y
        self.X1 = 0
        self.X2 = self.Width

    def Move(self):
        """
        move floor so it looks like its scrolling
        :return: None
        """
        self.X1 -= self.Vel
        self.X2 -= self.Vel
        if self.X1 + self.Width < 0:
            self.X1 = self.X2 + self.Width

        if self.X2 + self.Width < 0:
            self.X2 = self.X1 + self.Width

    def Draw(self, Win):
        """
        Draw the floor. This is two images that move together.
        :param win: the pygame surface/window
        :return: None
        """
        Win.blit(self.Img, (self.X1, self.Y))
        Win.blit(self.Img, (self.X2, self.Y))


def BlitRotateCenter(Surf, Image, TopLeft, Angle):
    """
    Rotate a surface and blit it to the window
    :param surf: the surface to blit to
    :param image: the image surface to rotate
    :param topLeft: the top left position of the image
    :param angle: a float value for angle
    :return: None
    """
    RotatedImage = pygame.transform.rotate(Image, Angle)
    NewRect = RotatedImage.get_rect(center = Image.get_rect(topleft = TopLeft).center)

    Surf.blit(RotatedImage, NewRect.topleft)

def DrawWindow(Win, Birds, Pipes, Base, Score, Gen, PipeInd):
    """
    draws the windows for the main game loop
    :param win: pygame window surface
    :param bird: a Bird object
    :param pipes: List of pipes
    :param score: score of the game (int)
    :param gen: current generation
    :param pipe_ind: index of closest pipe
    :return: None
    """
    if Gen == 0:
        Gen = 1
    Win.blit(BgImg, (0,0))

    for Pipe in Pipes:
        Pipe.Draw(Win)

    Base.Draw(Win)
    for Bird in Birds:
        # draw lines from bird to pipe
        if DrawLines:
            try:
                pygame.draw.line(Win, (255,0,0), (Bird.X+Bird.Img.get_width()/2, Bird.Y + Bird.Img.get_height()/2), (Pipes[PipeInd].X + Pipes[PipeInd].PipeTop.get_width()/2, Pipes[PipeInd].Height), 5)
                pygame.draw.line(Win, (255,0,0), (Bird.X+Bird.Img.get_width()/2, Bird.Y + Bird.Img.get_height()/2), (Pipes[PipeInd].X + Pipes[PipeInd].PipeBottom.get_width()/2, Pipes[PipeInd].Bottom), 5)
            except:
                pass
        # draw bird
        Bird.Draw(Win)

    # score
    ScoreLabel = StatFont.render("Score: " + str(Score),1,(255,255,255))
    Win.blit(ScoreLabel, (WinWidth - ScoreLabel.get_width() - 15, 10))

    # generations
    ScoreLabel = StatFont.render("Gens: " + str(Gen-1),1,(255,255,255))
    Win.blit(ScoreLabel, (10, 10))

    # alive
    ScoreLabel = StatFont.render("Alive: " + str(len(Birds)),1,(255,255,255))
    Win.blit(ScoreLabel, (10, 50))

    pygame.display.update()


def EvalGenomes(Genomes, Config):
    """
    runs the simulation of the current population of
    birds and sets their fitness based on the distance they
    reach in the game.
    """
    global Win, Gen
    Win = WIN
    Gen += 1

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # bird object that uses that network to play
    Nets = []
    Birds = []
    Ge = []
    for GenomeId, Genome in Genomes:
        Genome.fitness = 0  # start with fitness level of 0
        Net = neat.nn.FeedForwardNetwork.create(Genome, Config)
        Nets.append(Net)
        Birds.append(Bird(230,350))
        Ge.append(Genome)

    Base = Base(Floor)
    Pipes = [Pipe(700)]
    Score = 0

    Clock = pygame.time.Clock()

    Run = True
    while Run and len(Birds) > 0:
        Clock.tick(30)

        for Event in pygame.event.get():
            if Event.type == pygame.QUIT:
                Run = False
                pygame.quit()
                quit()
                break

        PipeInd = 0
        if len(Birds) > 0:
            if len(Pipes) > 1 and Birds[0].X > Pipes[0].X + Pipes[0].PipeTop.get_width():  # determine whether to use the first or second
                PipeInd = 1                                                                 # pipe on the screen for neural network input

        for X, Bird in enumerate(Birds):  # give each bird a fitness of 0.1 for each frame it stays alive
            Ge[X].fitness += 0.1
            Bird.Move()

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            Output = Nets[Birds.index(Bird)].activate((Bird.Y, abs(Bird.Y - Pipes[PipeInd].Height), abs(Bird.Y - Pipes[PipeInd].Bottom)))

            if Output[0] > 0.5:  # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
                Bird.Jump()

        Base.Move()

        Rem = []
        AddPipe = False
        for Pipe in Pipes:
            Pipe.Move()
            # check for collision
            for Bird in Birds:
                if Pipe.Collide(Bird, Win):
                    Ge[Birds.index(Bird)].fitness -= 1
                    Nets.pop(Birds.index(Bird))
                    Ge.pop(Birds.index(Bird))
                    Birds.pop(Birds.index(Bird))

            if Pipe.X + Pipe.PipeTop.get_width() < 0:
                Rem.append(Pipe)

            if not Pipe.Passed and Pipe.X < Bird.X:
                Pipe.Passed = True
                AddPipe = True

        if AddPipe:
            Score += 1
            # can add this line to give more reward for passing through a pipe (not required)
            for Genome in Ge:
                Genome.fitness += 5
            Pipes.append(Pipe(WinWidth))

        for R in Rem:
            Pipes.remove(R)

        for Bird in Birds:
            if Bird.Y + Bird.Img.get_height() - 10 >= Floor or Bird.Y < -50:
                Nets.pop(Birds.index(Bird))
                Ge.pop(Birds.index(Bird))
                Birds.pop(Birds.index(Bird))

        DrawWindow(WIN, Birds, Pipes, Base, Score, Gen, PipeInd)

        # break if score gets large enough
        '''if score > 20:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            break'''


def Run(ConfigFile):
    """
    runs the NEAT algorithm to train a neural network to play flappy bird.
    :param config_file: location of config file
    :return: None
    """
    Config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         ConfigFile)

    # Create the population, which is the top-level object for a NEAT run.
    P = neat.Population(Config)

    # Add a stdout reporter to show progress in the terminal.
    P.add_reporter(neat.StdOutReporter(True))
    Stats = neat.StatisticsReporter()
    P.add_reporter(Stats)
    #p.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    Winner = P.run(EvalGenomes, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(Winner))


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    LocalDir = os.path.dirname(__file__)
    ConfigPath = os.path.join(LocalDir, 'config-feedforward.txt')
    Run(ConfigPath)
