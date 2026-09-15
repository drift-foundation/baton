from demo.units import hours_to_seconds, minutes_to_seconds

assert hours_to_seconds(0) == 0
assert hours_to_seconds(1) == 3600
assert hours_to_seconds(2) == 7200
assert minutes_to_seconds(0) == 0
assert minutes_to_seconds(2) == 120
print("hours and minutes checks passed")
