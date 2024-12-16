import pygame
import random
import os
import time
import neat
import visualize
import pickle
pygame.font.init() # init font

WinWidth = 600
WinHeight = 800
Floor = 730
StatFont = pygame.font.SysFont("comicsans", 50)
EndFont = pygame.font.SysFont("comicsans", 70)
EndFont = False

WIN = pygame.display.set_mode((WinWidth, WinHeight))
pygame.display.set_caption("Flappy Bird")

PipeImg = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
BgImg = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
BirdImage = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
BaseImg = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

Gen = 0

class Bird:
  """
  Bird class representing the flappy bird
  """
  MaxRotation = 25
  Imgs = BirdImage
  RotVel = 20
  AnimationTime = 5

  def __init__(self, x, y):
    """
    Initialize the object
    :param x: starting x pos (int)
    :param y: starting y pos (int)
    :return: None
    """
    self.x = x
    self.y = y
    self.tilt = 0 # degrees to tilt
    self.tick_count = 0
    self.vel = 0
    self.height = self.y
    self.img_count = 0
    self.img = self.Imgs[0]

  def Jump(self):
    """
    make the bird jump
    :return: None
    """
    self.vel = -10.5
    self.tick_count = 0
    self.height = self.y

  def Move(self):
    """
    make the bird move
    :return: None
    """
    self.tick_count += 1

    # for downward acceleration
    Displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2 # calculate displacement

    # terminal velocity
    if Displacement >= 16:
      Displacement = (Displacement/abs(Displacement)) * 16

    if Displacement < 0:
      Displacement -= 2

    self.y = self.y + Displacement

    if Displacement < 0 or self.y < self.height + 50: # tilt up
      if self.tilt < self.MaxRotation:
        self.tilt = self.MaxRotation
    else: # tilt down
      if self.tilt > -90:
        self.tilt -= self.RotVel

  def Draw(self, win):
    """
    draw the bird
    :param win: pygame window or surface
    :return: None
    """
    self.img_count += 1

    # For animation of bird, loop through three images
    if self.img_count <= self.AnimationTime:
      self.img = self.Imgs[0]
    elif self.img_count <= self.AnimationTime*2:
      self.img = self.Imgs[1]
    elif self.img_count <= self.AnimationTime*3:
      self.img = self.Imgs[2]
    elif self.img_count <= self.AnimationTime*4:
      self.img = self.Imgs[1]
    elif self.img_count == self.AnimationTime*4 + 1:
      self.img = self.Imgs[0]
      self.img_count = 0

    # so when bird is nose diving it isn't flapping
    if self.tilt <= -80:
      self.img = self.Imgs[1]
      self.img_count = self.AnimationTime*2


    # tilt the bird
    BLitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

  def GetMask(self):
    """
    gets the mask for the current image of the bird
    :return: None
    """
    return pygame.mask.from_surface(self.img)


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
    self.x = x
    self.height = 0

    # where the top and bottom of the pipe is
    self.top = 0
    self.bottom = 0

    self.PIPE_TOP = pygame.transform.flip(PipeImg, False, True)
    self.PIPE_BOTTOM = PipeImg

    self.passed = False

    self.SetHeight()

  def SetHeight(self):
    """
    set the height of the pipe, from the top of the screen
    :return: None
    """
    self.height = random.randrange(50, 450)
    self.top = self.height - self.PIPE_TOP.get_height()
    self.bottom = self.height + self.Gap

  def Move(self):
    """
    move pipe based on vel
    :return: None
    """
    self.x -= self.Vel

  def Draw(self, win):
    """
    draw both the top and bottom of the pipe
    :param win: pygame window/surface
    :return: None
    """
    # draw top
    win.blit(self.PIPE_TOP, (self.x, self.top))
    # draw bottom
    win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


  def Collide(self, bird, win):
    """
    returns if a point is colliding with the pipe
    :param bird: Bird object
    :return: Bool
    """
    BirdMask = bird.get_mask()
    TopMask = pygame.mask.from_surface(self.PIPE_TOP)
    BottomMask = pygame.mask.from_surface(self.PIPE_BOTTOM)
    TopOffset = (self.x - bird.x, self.top - round(bird.y))
    BottomOffset = (self.x - bird.x, self.bottom - round(bird.y))

    BPoint = BirdMask.overlap(BottomMask, BottomOffset)
    TPoint = BirdMask.overlap(TopMask,TopOffset)

    if BPoint or TPoint:
      return True

    return False

class Base:
  """
  Represnts the moving Floor of the game
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
    self.y = y
    self.x1 = 0
    self.x2 = self.Width

  def Move(self):
    """
    move Floor so it looks like its scrolling
    :return: None
    """
    self.x1 -= self.Vel
    self.x2 -= self.Vel
    if self.x1 + self.Width < 0:
      self.x1 = self.x2 + self.Width

    if self.x2 + self.Width < 0:
      self.x2 = self.x1 + self.Width

  def Draw(self, win):
    """
    Draw the Floor. This is two images that move together.
    :param win: the pygame surface/window
    :return: None
    """
    win.blit(self.Img, (self.x1, self.y))
    win.blit(self.Img, (self.x2, self.y))


def BLitRotateCenter(surf, image, topleft, angle):
  """
  Rotate a surface and blit it to the window
  :param surf: the surface to blit to
  :param image: the image surface to rotate
  :param topLeft: the top left position of the image
  :param angle: a float value for angle
  :return: None
  """
  rotated_image = pygame.transform.rotate(image, angle)
  new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

  surf.blit(rotated_image, new_rect.topleft)

def DrawWindow(win, birds, pipes, base, score, gen, pipe_ind):
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
  if gen == 0:
    gen = 1
  win.blit(BgImg, (0,0))

  for pipe in pipes:
    pipe.draw(win)

  base.draw(win)
  for bird in birds:
    # draw lines from bird to pipe
    if EndFont:
      try:
        pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
        pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
      except:
        pass
    # draw bird
    bird.draw(win)

  # score
  score_label = StatFont.render("Score: " + str(score),1,(255,255,255))
  win.blit(score_label, (WinWidth - score_label.get_width() - 15, 10))

  # generations
  score_label = StatFont.render("Gens: " + str(gen-1),1,(255,255,255))
  win.blit(score_label, (10, 10))

  # alive
  score_label = StatFont.render("Alive: " + str(len(birds)),1,(255,255,255))
  win.blit(score_label, (10, 50))

  pygame.display.update()


def EvalGenomes(genomes, config):
  """
  runs the simulation of the current population of
  birds and sets their fitness based on the distance they
  reach in the game.
  """
  global WIN, Gen
  Win = WIN
  Gen += 1

  # start by creating lists holding the genome itself, the
  # neural network associated with the genome and the
  # bird object that uses that network to play
  Nets = []
  Birds = []
  GE = []
  for genome_id, genome in genomes:
    genome.fitness = 0 # start with fitness level of 0
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    Nets.append(net)
    Birds.append(Bird(230,350))
    GE.append(genome)

  Base = Base(Floor)
  Pipes = [Pipe(700)]
  Score = 0

  Clock = pygame.time.Clock()

  Run = True
  while Run and len(Birds) > 0:
    Clock.tick(30)

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        Run = False
        pygame.quit()
        quit()
        break

    PipeIND = 0
    if len(Birds) > 0:
      if len(Pipes) > 1 and Birds[0].x > Pipes[0].x + Pipes[0].PIPE_TOP.get_width(): # determine whether to use the first or second
        PipeIND = 1                                 # pipe on the screen for neural network input

    for x, bird in enumerate(Birds): # give each bird a fitness of 0.1 for each frame it stays alive
      GE[x].fitness += 0.1
      bird.move()

      # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
      Output = Nets[Birds.index(bird)].activate((bird.y, abs(bird.y - Pipes[PipeIND].height), abs(bird.y - Pipes[PipeIND].bottom)))

      if Output[0] > 0.5: # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
        bird.jump()

    Base.Move()

    Rem = []
    AddPipe = False
    for pipe in Pipes:
      pipe.Move()
      # check for collision
      for bird in Birds:
        if pipe.Collide(bird, Win):
          GE[Birds.index(bird)].fitness -= 1
          Nets.pop(Birds.index(bird))
          GE.pop(Birds.index(bird))
          Birds.pop(Birds.index(bird))

      if pipe.x + pipe.PIPE_TOP.get_width() < 0:
        Rem.append(pipe)

      if not pipe.passed and pipe.x < bird.x:
        pipe.passed = True
        AddPipe = True

    if AddPipe:
      Score += 1
      # can add this line to give more reward for passing through a pipe (not required)
      for genome in GE:
        genome.fitness += 5
      Pipes.append(Pipe(WinWidth))

    for r in Rem:
      Pipes.remove(r)

    for bird in Birds:
      if bird.y + bird.img.get_height() - 10 >= Floor or bird.y < -50:
        Nets.pop(Birds.index(bird))
        GE.pop(Birds.index(bird))
        Birds.pop(Birds.index(bird))

    DrawWindow(WIN, Birds, Pipes, Base, Score, Gen, PipeIND)

    # break if score gets large enough
    '''if score > 20:
      pickle.dump(nets[0],open("best.pickle", "wb"))
      break'''


def Run(config_file):
  """
  runs the NEAT algorithm to train a neural network to play flappy bird.
  :param config_file: location of config file
  :return: None
  """
  Config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

  # Create the population, which is the top-level object for a NEAT run.
  P = neat.Population(Config)

  # Add a stdout reporter to show progress in the terminal.
  P.add_reporter(neat.StdOutReporter(True))
  stats = neat.StatisticsReporter()
  P.add_reporter(stats)
  #p.add_reporter(neat.Checkpointer(5))

  # Run for up to 50 generations.
  Winner = P.run(EvalGenomes, 50)

  # show final stats
  print('\nBest genome:\n{!s}'.format(Winner))


if __name__ == '__main__':
  # Determine path to configuration file. This path manipulation is
  # here so that the script will run successfully regardless of the
  # current working directory.
  local_dir = os.path.dirname(__file__)
  ConfigPath = os.path.join(local_dir, 'ConfigFeedForward.txt')
  Run(ConfigPath)