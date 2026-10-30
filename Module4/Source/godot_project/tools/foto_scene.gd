extends SceneTree
## Saves screenshots of Main.tscn for the README (needs a window, not --headless).
## Run: $GODOT --path godot_project --resolution 1280x720 --script res://tools/foto_scene.gd -- <out_dir>
## Frames 150 and 520 are taken from the spline camera, the last one from the overview camera.

const SHOTS := {150: "godot_jalur_1.png", 520: "godot_jalur_2.png"}
const OVERVIEW_AT := 560

var _frame := 0
var _out := ""
var _main: Node


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	_out = args[0] if args.size() > 0 else OS.get_user_data_dir()
	_main = load("res://scenes/Main.tscn").instantiate()
	root.add_child(_main)
	current_scene = _main


func _process(_delta: float) -> bool:
	_frame += 1
	if SHOTS.has(_frame):
		_save(SHOTS[_frame])
	if _frame == OVERVIEW_AT:
		_main.get_node("OverviewCamera").make_current()
	if _frame == OVERVIEW_AT + 10:
		_save("godot_overview.png")
		return true
	return false


func _save(name: String) -> void:
	var path := _out.path_join(name)
	root.get_texture().get_image().save_png(path)
	print("FOTO ", path)
