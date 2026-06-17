import pygame


class CollisionSystem:
    def __init__(self, campus):
        self.campus = campus

        # Solid building areas.
        self.solids = [
            campus.main_block.copy(),
            campus.ncc_block.copy(),
            campus.mech_block.copy(),
            campus.library.copy(),
            campus.ai_block.copy(),
            campus.ece_block.copy(),
        ]

        # The AI entrance must remain accessible.
        self.ai_entrance = campus.ai_entrance.copy()

    def collides(self, rect):
        """
        Return True when the player rectangle touches
        a solid building.
        """

        for building in self.solids:
            # Leave the AI entrance open.
            if building == self.campus.ai_block:
                blocked = building.copy()

                # Remove the entrance opening from the left wall.
                top = self.ai_entrance.top
                bottom = self.ai_entrance.bottom

                upper = pygame.Rect(
                    blocked.left,
                    blocked.top,
                    blocked.width,
                    top - blocked.top,
                )

                lower = pygame.Rect(
                    blocked.left,
                    bottom,
                    blocked.width,
                    blocked.bottom - bottom,
                )

                if rect.colliderect(upper):
                    return True

                if rect.colliderect(lower):
                    return True

                # Block the right side of the AI building.
                right = pygame.Rect(
                    blocked.left + 25,
                    top,
                    blocked.width - 25,
                    bottom - top,
                )

                if rect.colliderect(right):
                    return True

            elif rect.colliderect(building):
                return True

        return False