@tool
extends Node3D
## The KayKit Knight (CC0, assets/kaykit/, see assets/LICENSE.md) in my room.
## Only the body parts are shown; the pack hangs every weapon and shield on the
## rig at once.
##
## Walking_A is an in-place clip: the feet swing but the root never moves. With
## `walk` on, the Knight is moved by root motion read from the clip itself: each frame
## the animation is advanced by hand, and the Knight steps forward by exactly how far
## its planted foot (the lower one) moved back in the skeleton's space, so that foot
## stays where it is on the floor. No walking speed is typed anywhere (T11, pitfall c).
## It walks from `lane_from` to `lane_to`, turns round about y, and walks back.

@export var animation: String = "Idle"
@export var walk_animation: String = "Walking_A"
@export var walk: bool = false
@export var lane_from: Vector3 = Vector3(0.15, 0, -0.6)
@export var lane_to: Vector3 = Vector3(0.15, 0, 0.6)
@export var turn_seconds: float = 0.6
@export var keep_meshes: PackedStringArray = ["Knight_Body", "Knight_Head", "Knight_Helmet", "Knight_Cape",
	"Knight_ArmLeft", "Knight_ArmRight", "Knight_LegLeft", "Knight_LegRight"]

var player: AnimationPlayer
var skeleton: Skeleton3D
var feet: Array[int] = []
var _goal := Vector3.ZERO
var _turn_left := 0.0
var _yaw_from := 0.0
var _yaw_to := 0.0


func _ready() -> void:
	for m in find_children("*", "MeshInstance3D", true, false):
		m.visible = m.name in keep_meshes
	var players := find_children("*", "AnimationPlayer", true, false)
	player = players[0] if players.size() > 0 else null
	var skeletons := find_children("*", "Skeleton3D", true, false)
	skeleton = skeletons[0] if skeletons.size() > 0 else null
	if player == null or Engine.is_editor_hint():
		return
	if walk and skeleton != null:
		feet = [skeleton.find_bone("foot.l"), skeleton.find_bone("foot.r")]
		player.get_animation(walk_animation).loop_mode = Animation.LOOP_LINEAR
		player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		player.play(walk_animation)
		position = lane_from
		_face(lane_to)
		_goal = lane_to
	else:
		player.get_animation(animation).loop_mode = Animation.LOOP_LINEAR
		player.play(animation)


func _process(delta: float) -> void:
	if Engine.is_editor_hint() or not walk or feet.is_empty():
		return
	if _turn_left > 0.0:
		_turn_left = maxf(0.0, _turn_left - delta)
		_set_yaw(lerpf(_yaw_to, _yaw_from, _turn_left / turn_seconds))
		player.advance(delta)  # keep stepping in place while turning
		return
	var foot := planted_foot()
	var before := skeleton.get_bone_global_pose(foot).origin
	player.advance(delta)
	var after := skeleton.get_bone_global_pose(foot).origin
	# skeleton space: +z is the Knight's forward; basis carries its yaw and its 0.16 scale
	position += basis * Vector3(0, 0, before.z - after.z)
	if (_goal - position).dot(basis.z) <= 0.0:
		var next := lane_from if _goal == lane_to else lane_to
		_yaw_from = rotation.y
		_yaw_to = _yaw_of(next - position)
		_turn_left = turn_seconds
		_goal = next


## The foot carrying the Knight: the lower of the two in skeleton space.
func planted_foot() -> int:
	var l := skeleton.get_bone_global_pose(feet[0]).origin.y
	var r := skeleton.get_bone_global_pose(feet[1]).origin.y
	return feet[0] if l <= r else feet[1]


func _face(target: Vector3) -> void:
	_set_yaw(_yaw_of(target - position))


func _yaw_of(direction: Vector3) -> float:
	return atan2(direction.x, direction.z)  # yaw that turns +z (the Knight's forward) onto direction


func _set_yaw(yaw: float) -> void:
	var s := basis.get_scale()
	basis = Basis(Vector3.UP, yaw).scaled(s)
