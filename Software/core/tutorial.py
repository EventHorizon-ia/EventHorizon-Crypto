import pygame

def desenhar_tutorial(screen, WIDTH, HEIGHT, font, estado_ui):

    screen.fill((5, 5, 10))

    step = estado_ui.get("tutorial_step", 0)

    blocos = [

        # STEP 0
        [
            "[SYSTEM INITIALIZED]",
            "",
            "> Welcome, operator.",
            "",
            "This is a dynamic energy simulation system.",
            "",
            "You are not just observing.",
            "You CONTROL the system.",
            "",
            "[PRESS ENTER]"
        ],

        # STEP 1
        [
            "Each UNIT is an active entity.",
            "",
            "- stores energy",
            "- interacts with others",
            "- evolves over time",
            "",
            "They form patterns automatically.",
            "",
            "[PRESS ENTER]"
        ],

        # STEP 2
        [
            "You can manipulate the system.",
            "",
            "Try commands in terminal:",
            "",
            "c",
            "list units",
            "",
            "Press ESC to open terminal.",
            "",
            "[PRESS ENTER]"
        ],

        # STEP 3
        [
            "Energy flows through PULSES.",
            "",
            "Try this:",
            "",
            "send pulse 1 2",
            "",
            "Watch how the system reacts.",
            "",
            "[PRESS ENTER]"
        ],

        # STEP 4
        [
            "Advanced systems emerge from interactions.",
            "",
            "Examples:",
            "- balance (stabilization)",
            "- flow (path finding)",
            "- crypto (dynamic data)",
            "",
            "[PRESS ENTER TO START]"
        ]
    ]

    textos = blocos[min(step, len(blocos)-1)]

    y = 120
    for t in textos:
        txt = font.render(t, True, (0, 255, 200))
        screen.blit(txt, (100, y))
        y += 20