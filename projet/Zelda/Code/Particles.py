import pygame
from Support import import_folder
from random import choice
import os


# This is for file (images specifically) importing (This line changes the directory to where the project is saved)
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class AnimationPlayer:
    def __init__(self):
        self.frames = {
			# Magic
			"flame": import_folder("../Graphics/Particles/Flame/frames"),
			"aura": import_folder("../Graphics/Particles/Aura"),
			"heal": import_folder("../Graphics/Particles/Heal/frames"),

			# Attacks
			"claw": import_folder("../Graphics/Particles/Claw"),
			"slash": import_folder("../Graphics/Particles/Slash"),
			"sparkle": import_folder("../Graphics/Particles/sparkle"),
			"leaf_attack": import_folder("../Graphics/Particles/leaf_attack"),
			"thunder": import_folder("../Graphics/Particles/Thunder"),

			# Monster Deaths
			"squid": import_folder("../Graphics/Particles/smoke_orange"),
			"raccoon": import_folder("../Graphics/Particles/Raccoon"),
			"spirit": import_folder("../Graphics/Particles/Nova"),
			"bamboo": import_folder("../Graphics/Particles/Bamboo"),

			# Leafs
			"leaf":(
				import_folder("../Graphics/Particles/leaf1"),
				import_folder("../Graphics/Particles/leaf2"),
				import_folder("../Graphics/Particles/leaf3"),
				import_folder("../Graphics/Particles/leaf4"),
				import_folder("../Graphics/Particles/leaf5"),
				import_folder("../Graphics/Particles/leaf6"),
				self.reflect_images(import_folder("../Graphics/Particles/leaf1")),
				self.reflect_images(import_folder("../Graphics/Particles/leaf2")),
				self.reflect_images(import_folder("../Graphics/Particles/leaf3")),
				self.reflect_images(import_folder("../Graphics/Particles/leaf4")),
				self.reflect_images(import_folder("../Graphics/Particles/leaf5")),
				self.reflect_images(import_folder("../Graphics/Particles/leaf6"))
				)
			}

    def reflect_images(self, frames):
        new_frames = []

        for frame in frames:
            flipped_frame = pygame.transform.flip(frame, True, False)
            new_frames.append(flipped_frame)
        return new_frames

    def create_grass_particles(self, pos, groups):
        animation_frames = choice(self.frames["leaf"])
        ParticleEffect(pos, animation_frames, groups)

    def create_particles(self, animation_type, pos, groups):
        animation_frames = self.frames[animation_type]
        ParticleEffect(pos, animation_frames, groups)


class ParticleEffect(pygame.sprite.Sprite):
    def __init__(self, pos, animation_frames, groups):
        super().__init__(groups)
        self.sprite_type = "magic"
        self.frame_index = 0
        self.animation_speed = 0.15
        self.frames = animation_frames
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center = pos)

    def animate(self):
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]

    def update(self):
        self.animate()