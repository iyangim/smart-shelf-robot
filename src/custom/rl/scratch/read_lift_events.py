import os
import glob
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

log_dir = "/home/iyangim/franka_isaaclab/logs/skrl/franka_lift/2026-06-19_11-48-19_ppo_torch"
event_files = glob.glob(os.path.join(log_dir, "events.out.tfevents.*"))

if not event_files:
    print("No event files found.")
    exit(1)

event_file = event_files[0]
ea = EventAccumulator(event_file)
ea.Reload()

tags = [
    "Reward / Total reward (mean)",
    "Episode_Reward/reaching_object",
    "Episode_Reward/lifting_object",
    "Episode_Reward/object_goal_tracking",
    "Episode_Reward/object_goal_tracking_fine_grained",
    "Episode_Reward/action_rate",
    "Episode_Reward/joint_vel",
    "Loss / Policy loss",
    "Loss / Value loss",
]

for tag in tags:
    try:
        events = ea.Scalars(tag)
        if events:
            print(f"\nTag: {tag}")
            for event in events[-5:]:
                print(f"  Step {event.step}: Value {event.value:.4f}")
    except KeyError:
        print(f"\nTag: {tag} not recorded yet.")
