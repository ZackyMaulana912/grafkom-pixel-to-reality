@tool
extends Node3D
## The KayKit Knight (CC0, assets/kaykit/, see assets/LICENSE.md) standing in my room.
## Only the body parts are shown; the pack hangs every weapon and shield on the
## rig at once. Plays `animation` while the game runs.

@export var animation: String = "Idle"
@export var keep_meshes: PackedStringArray = ["Knight_Body", "Knight_Head", "Knight_Helmet", "Knight_Cape",
	"Knight_ArmLeft", "Knight_ArmRight", "Knight_LegLeft", "Knight_LegRight"]

var player: AnimationPlayer


func _ready() -> void:
	for m in find_children("*", "MeshInstance3D", true, false):
		m.visible = m.name in keep_meshes
	var players := find_children("*", "AnimationPlayer", true, false)
	player = players[0] if players.size() > 0 else null
	if player != null and not Engine.is_editor_hint():
		player.get_animation(animation).loop_mode = Animation.LOOP_LINEAR
		player.play(animation)
