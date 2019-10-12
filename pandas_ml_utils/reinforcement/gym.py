import pandas as pd
import numpy as np
import gym
from gym import spaces
from typing import Tuple, Callable, List

from ..model.features_and_Labels import FeaturesAndLabels

INIT_ACTION = -1


class RowWiseGym(gym.Env):

    def __init__(self,
                 environment: Tuple[np.ndarray, np.ndarray],
                 features_and_labels: FeaturesAndLabels,
                 action_reward_functions: List[Callable[[np.ndarray], float]],
                 reward_range: Tuple[int, int]):
        super().__init__()
        self.environment = environment
        self.reward_range = reward_range
        self.action_reward_functions = action_reward_functions

        # start at the beginning of the frame
        self.state = 0

        # define spaces
        self.action_space = spaces.Discrete(len(action_reward_functions))
        self.observation_space = spaces.Box(low=-1, high=1, shape=features_and_labels.shape()[0], dtype=np.float16)

        # define history
        self.reward_history = []

    metadata = {'render.modes': ['human']}

    def reset(self):
        # Reset the state of the environment to an initial state
        return self.step(INIT_ACTION)[0]

    def step(self, action):
        # Execute one time step within the environment
        if action is not INIT_ACTION:
            reward = self.action_reward_functions[action](self.environment[1][self.state])
            self.reward_history.append(reward)
            self.state += 1
        else:
            reward = 0
            self.state = 0

        done = self.state >= len(self.environment[0])
        obs = self.environment[0][self.state if not done else None]

        return obs, reward, done, {}

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        # TODO print something
        #print("something")
        pass

    def get_reward_history(self):
        return np.array(self.reward_history)