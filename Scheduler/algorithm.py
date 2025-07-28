from collections import defaultdict
from functools import lru_cache
import random
from math import ceil 
import heapq

@lru_cache(maxsize=None)
def get_valid_day_slot_combinations(days_tuple, time_slots_str, block_size):
    days = list(days_tuple)
    time_slots = time_slots_str.split(',')
    valid_combinations = []

    for day in days:
        for i in range(len(time_slots) - block_size + 1):
            slots = time_slots[i:i+block_size]
            # Check if slots are consecutive (e.g., 09:00 - 09:55, 10:00 - 10:55)
            if all(
                int(slots[j].split(':')[0]) + 1 == int(slots[j+1].split(':')[0])
                for j in range(len(slots) - 1)
            ):
                valid_combinations.append((day, i))
    
    return valid_combinations


def get_time_priority(slot):
    """Prioritize morning/late afternoon slots (3=high, 1=low)."""
    hour = int(slot.split(':')[0])
    return 3 if (8 <= hour < 10 or hour >= 16) else 2 if (10 <= hour < 14) else 1

def get_course_priority(course_code, lecturers_courses_mapping, enrollment_breakdown, course_class_map):
    """Sort courses by: 1. Fewer lecturers available, 2. Higher enrollment."""
    lecturer_count = len(lecturers_courses_mapping.get(course_code, []))
    enrollments = [
        len(enrollment_breakdown.get(course_code, {}).get(cls, []))
        for cls in course_class_map.get(course_code, [])
    ]
    max_enrollment = max(enrollments) if enrollments else 0
    return (lecturer_count, -max_enrollment)  # Low lecturer count first

def get_course_lecturer(course_code, lecturers_courses_mapping, lecturer_availability, 
                        lecturer_bookings, day, slots, lecturer_assignments):
    """Select lecturer with availability or assume full availability if none given."""
    lecturers = lecturers_courses_mapping.get(course_code, [])
    if not lecturers:
        return None

    def is_fully_available(lecturer):
        available = lecturer_availability.get(lecturer, {}).get(day)
        if available is None:
            return True  
        return set(available).issuperset(set(slots))

    lecturers.sort(key=lambda l: (
        0 if is_fully_available(l) else 1,
        lecturer_assignments.get(l, 0)
    ))

    for lecturer in lecturers:
        if is_available(lecturer_bookings[lecturer], day, slots) and is_fully_available(lecturer):
            return lecturer
    return None


# def select_room(class_enrollment, day, slots, room_bookings, room_size, room_usage_count):
#     """Pick best room: 1. Fits enrollment, 2. Minimal overcapacity, 3. Least used."""
#     suitable_rooms = [r for r in room_size if room_size[r] >= class_enrollment]
#     suitable_rooms.sort(key=lambda r: (
#         room_size[r] - class_enrollment,
#         room_usage_count[r],
#         random.random()
#     ))
#     for room in suitable_rooms:
#         if is_available(room_bookings[room], day, slots):
#             return room
#     return None

def select_room(
    class_size,
    available_rooms,
    room_size,
    course_code,
    course_type_map,
    room_type_map,
    lab_room_map,
    course_lab_type_map,
    room_usage_count,
    room_bookings,
    day,
    slots):
    """Improved room selection with strict prioritization of large classes"""
    
    course_type = course_type_map.get(course_code, "lecture")
    is_large_class = class_size >= 200
    
    # --- STAGE 1: Filter by room type and capacity ---
    if course_type == "practical":
        required_lab_type = course_lab_type_map.get(course_code)
        suitable_rooms = [
            r for r in available_rooms
            if (room_type_map.get(r) == "laboratory" )and 
                required_lab_type in lab_room_map.get(r, []) and
                room_size[r] >= class_size
        ]
    else:
        suitable_rooms = [
            r for r in available_rooms
            if (room_type_map.get(r) in {"lecture hall", "classroom", "auditorium"}) and
                room_size[r] >= class_size and
                (not is_large_class or room_type_map.get(r) == "lecture hall") and
                (is_large_class or room_size[r] <= max(class_size * 2, 100))  # 50% utilization rule
        ]
    
    # --- STAGE 2: Prioritization ---
    # For large classes: prefer largest available lecture halls first
    if is_large_class:
        suitable_rooms.sort(key=lambda r: (
            -room_size[r],  # Largest rooms first
            room_usage_count[r]  # Then least used
        ))
    # For small classes: prefer smallest suitable rooms
    else:
        suitable_rooms.sort(key=lambda r: (
            room_size[r],  # Smallest rooms first
            room_usage_count[r]  # Then least used
        ))
    
    # --- STAGE 3: Availability Check ---
    for room in suitable_rooms:
        if is_available(room_bookings[room], day, slots):
            return room
    
    # --- FALLBACK: Relax constraints if no room found ---
    if not suitable_rooms and is_large_class:
        # For large classes: try any large enough room if lecture halls are full
        fallback_rooms = [
            r for r in available_rooms
            if room_size[r] >= class_size and
               room_type_map.get(r) in {"lecture hall", "auditorium"}
        ]
        fallback_rooms.sort(key=lambda r: (
            -room_size[r],
            room_usage_count[r]
        ))
        for room in fallback_rooms:
            if is_available(room_bookings[room], day, slots):
                return room
    
    return None


def is_available(booking_map, day, slots):
    """Check if all slots on a day are free."""
    return all(slot not in booking_map[day] for slot in slots)

def assign_slots(booking_map, day, slots):
    """Mark slots on a day as booked."""
    for slot in slots:
        booking_map[day].add(slot)

def unassign_slots(booking_map, day, slots):
    """Free slots on a day."""
    for slot in slots:
        booking_map[day].discard(slot)

def try_assign(room, day, slots, lecturer, assigned_class, class_enrollment,
              room_bookings, lecturer_bookings, class_bookings,
              lecturer_assignments, room_usage_count, schedule, unscheduled_courses,
              course_code, lecturers_courses_mapping, enrollment_breakdown, course_class_map):
    """Helper to handle assignments with conflict resolution."""
    # Try direct assignment first
    if (is_available(room_bookings[room], day, slots) and
        is_available(class_bookings[assigned_class], day, slots) and
        (not lecturer or is_available(lecturer_bookings[lecturer], day, slots))):
        
        assign_slots(room_bookings[room], day, slots)
        assign_slots(class_bookings[assigned_class], day, slots)
        if lecturer:
            assign_slots(lecturer_bookings[lecturer], day, slots)
            lecturer_assignments[lecturer] += 1
        
        room_usage_count[room] += 1
        schedule.append({
            'course': course_code,
            'class': assigned_class,
            'day': day,
            'slots': slots,
            'room': room,
            'lecturer': lecturer,
            'enrollment': class_enrollment
        })
        return True
    
    # If conflict exists, try unassigning lower-priority sessions
    for entry in sorted(schedule, key=lambda x: (-x['enrollment'], random.random())):
        if entry['enrollment'] < class_enrollment:  # Lower priority
            # Temporarily unassign
            unassign_slots(room_bookings[entry['room']], entry['day'], entry['slots'])
            unassign_slots(class_bookings[entry['class']], entry['day'], entry['slots'])
            if entry['lecturer']:
                unassign_slots(lecturer_bookings[entry['lecturer']], entry['day'], entry['slots'])
                lecturer_assignments[entry['lecturer']] -= 1
            
            # Try assigning new session
            if (is_available(room_bookings[room], day, slots) and \
               is_available(class_bookings[assigned_class], day, slots) and \
               (not lecturer or is_available(lecturer_bookings[lecturer], day, slots))):
                
                assign_slots(room_bookings[room], day, slots)
                assign_slots(class_bookings[assigned_class], day, slots)
                if lecturer:
                    assign_slots(lecturer_bookings[lecturer], day, slots)
                    lecturer_assignments[lecturer] += 1
                
                room_usage_count[room] += 1
                schedule.append({
                    'course': course_code,
                    'class': assigned_class,
                    'day': day,
                    'slots': slots,
                    'room': room,
                    'lecturer': lecturer,
                    'enrollment': class_enrollment
                })
                
                # Re-add unassigned entry to retry later
                heapq.heappush(unscheduled_courses, (
                    get_course_priority(entry['course'], lecturers_courses_mapping, 
                                      enrollment_breakdown, course_class_map),
                    entry['course'],
                    sum(len(s.split(' - ')) for s in entry['slots'])  # Estimate credits
                ))
                return True
            else:
                # Revert unassignment
                assign_slots(room_bookings[entry['room']], entry['day'], entry['slots'])
                assign_slots(class_bookings[entry['class']], entry['day'], entry['slots'])
                if entry['lecturer']:
                    assign_slots(lecturer_bookings[entry['lecturer']], entry['day'], entry['slots'])
                    lecturer_assignments[entry['lecturer']] += 1
    
    return False

def generate_complete_schedule(
    courses, course_class_map, enrollment_breakdown, room_size,
    lecturers_courses_mapping, lecturer_availability, rooms, days, time_slots,
     course_type_map, room_type_map, lab_room_map,
    course_lab_type_map,max_attempts=100,
):
    schedule = []
    room_bookings = defaultdict(lambda: defaultdict(set))
    lecturer_bookings = defaultdict(lambda: defaultdict(set))
    class_bookings = defaultdict(lambda: defaultdict(set))
    room_usage_count = defaultdict(int)
    lecturer_assignments = defaultdict(int)
    scheduling_issues = defaultdict(list)
    
    # Priority queue: courses with fewer lecturers & higher enrollment first
    course_queue = []
    for course_code, credit in courses.items():
        priority = get_course_priority(course_code, lecturers_courses_mapping, 
                                     enrollment_breakdown, course_class_map)
        heapq.heappush(course_queue, (priority, course_code, credit))
    
    unscheduled_courses = []
    attempt_counter = 0
    
    while course_queue or unscheduled_courses:
        if not course_queue:  # Retry unscheduled courses
            course_queue = unscheduled_courses
            unscheduled_courses = []
            attempt_counter += 1
            if attempt_counter > 3:  # Max 3 retry cycles
                break
            
        _, course_code, credit = heapq.heappop(course_queue)
        assigned_classes = course_class_map.get(course_code, [])
        blocks = [2] * (credit // 2) + ([1] if credit % 2 else [])
        
        for assigned_class in assigned_classes:
            class_enrollment = len(enrollment_breakdown.get(course_code, {}).get(assigned_class, []))
            if class_enrollment == 0:
                continue
            
            for block in blocks:
                combinations = get_valid_day_slot_combinations(tuple(days), ",".join(time_slots), block)
                combinations.sort(key=lambda x: (
                    -get_time_priority(time_slots[x[1]].split(' - ')[0]),
                    random.random()
                ))
                
                assigned = False
                for day, start_slot in combinations:
                    slots = time_slots[start_slot:start_slot + block]
                    
                    # Try both with and without lecturer constraint
                    lecturer_options = [True] if lecturers_courses_mapping.get(course_code) else [False]

                    for require_lecturer in lecturer_options:
                        lecturer = get_course_lecturer(
                            course_code, lecturers_courses_mapping, lecturer_availability,
                            lecturer_bookings, day, slots, lecturer_assignments
                        ) if require_lecturer else None
                        
                        if require_lecturer and not lecturer:
                            continue
                         
                        room = select_room(
                            class_enrollment,
                            rooms,
                            room_size,
                            course_code,
                            course_type_map,
                            room_type_map,
                            lab_room_map,
                            course_lab_type_map,
                            room_usage_count,
                            room_bookings,
                            day,
                            slots
                        )
                        if not room or not is_available(class_bookings[assigned_class], day, slots):
                            continue
                        
                        if try_assign(
                            room, day, slots, lecturer, assigned_class, class_enrollment,
                            room_bookings, lecturer_bookings, class_bookings,
                            lecturer_assignments, room_usage_count, schedule, unscheduled_courses,
                            course_code, lecturers_courses_mapping, enrollment_breakdown, course_class_map
                        ):
                            assigned = True
                            break
                    
                    if assigned:
                        break
                
                if not assigned:
                    heapq.heappush(unscheduled_courses, (
                        get_course_priority(course_code, lecturers_courses_mapping,
                                          enrollment_breakdown, course_class_map),
                        course_code,
                        credit
                    ))
                    scheduling_issues[course_code].append({
                        'class': assigned_class,
                        'block': block,
                        'reason': f"Failed after {max_attempts} attempts (will retry)"
                    })

    print(f"Generated schedule with {len(schedule)} sessions")
    print(f"Scheduling issues: {sum(len(v) for v in scheduling_issues.values())}")
    return schedule, scheduling_issues










def exam_schedule(
    student_enrollment,
    course_type,
    exam_days,
    exam_slots,
    room_size,
    room_dimensions,
    overflow_rooms,
    max_courses,
    proctors_in_center,
    proctors,
    proctors_availability,
    enrollment_breakdown
):
    # Initialization
    template_data = {}
    used_slot = set()
    exam_schedule = []

    room_usage = defaultdict(lambda: defaultdict(set))
    room_courses = defaultdict(lambda: defaultdict(set))
    proctor_used = defaultdict(lambda: defaultdict(set))
    extra_columns = defaultdict(list)
    available_space = defaultdict(lambda: defaultdict(int))
    assigned_courses = set()
    assigned_students_tracker = defaultdict(lambda: defaultdict(int))  
    global_proctor_slot_usage = defaultdict(set)
    manual_assignment_log = []

    student_enrollment_sorted = sorted(student_enrollment.items(), key=lambda x: x[1], reverse=True)
    rooms_sorted = sorted(room_size.items(), key=lambda x: x[1], reverse=True)

    # Split proctors into those with and without explicit availability
    proctors_with_availability = [p for p in proctors if p in proctors_availability]
    proctors_without_availability = [p for p in proctors if p not in proctors_availability]

    for course, course_size in student_enrollment_sorted:
        if 'lab' in course_type.get(course, '').lower():
            manual_assignment_log.append({
                'course': course,
                'unassigned_count': course_size,
                'reason': 'Lab practical to be scheduled manually'
            })
            continue

        unassigned = course_size
        rooms_used = []
        assigned_day = None
        assigned_slot = None

        all_day_slot_combo = [(d, s) for d in exam_days for s in exam_slots]
        random.shuffle(all_day_slot_combo)

        for day, slot in all_day_slot_combo:
            for room, _ in rooms_sorted:
                if room in overflow_rooms or room.startswith("Lab-"):
                    continue

                if (
                    len(room_courses[(day, slot)][room]) >= max_courses[room]
                    or course in room_courses[(day, slot)][room]
                    or any(r['room'] == room for r in rooms_used)
                ):
                    continue

                row_num = int(room_dimensions[room].split(' x ')[0])
                col_num = int(room_dimensions[room].split(' x ')[1])
                available_columns = set(range(col_num))
                used_columns = room_usage[(day, slot)][room]
                free_columns = available_columns - used_columns

                max_allowed_courses = max_courses[room]
                max_cols_for_course = col_num // max_allowed_courses

                if len(free_columns) < max_cols_for_course:
                    continue

                min_students_per_col = 0.75 * row_num
                required_students = (max_cols_for_course - 1) * row_num + min_students_per_col

                if unassigned >= required_students:
                    assigned = False
                    for class_code, ids in enrollment_breakdown.get(course, {}).items():
                        already_assigned = assigned_students_tracker[course][class_code]
                        remaining_students = ids[already_assigned:]

                        if not remaining_students:
                            continue

                        students_to_assign = min(unassigned, len(remaining_students), max_cols_for_course * row_num)
                        if students_to_assign == 0:
                            continue

                        assigned_ids = remaining_students[:students_to_assign]
                        assigned_students_tracker[course][class_code] += students_to_assign
                        unassigned -= students_to_assign

                        cols_to_use = set(sorted(free_columns)[:max_cols_for_course])

                        room_usage[(day, slot)][room].update(cols_to_use)
                        room_courses[(day, slot)][room].add(course)

                        rooms_used.append({
                            'room': room,
                            'columns_used': cols_to_use,
                            'student_ids': assigned_ids,
                            'class': class_code
                        })

                        assigned = True
                        break  

                    if not assigned:
                        continue

                    # Assign proctors - first try those with explicit availability
                    needed_proctors = proctors_in_center[room] - len(proctor_used[(day, slot)][room])
                    if needed_proctors > 0:
                        # First try proctors with explicit availability
                        for proctor in proctors_with_availability:
                            if (proctor not in global_proctor_slot_usage[(day, slot)] and 
                                day in proctors_availability[proctor]):
                                proctor_used[(day, slot)][room].add(proctor)
                                global_proctor_slot_usage[(day, slot)].add(proctor)
                                needed_proctors -= 1
                                if needed_proctors <= 0:
                                    break
                        
                        # Then try proctors without explicit availability if still needed
                        for proctor in proctors_without_availability:
                            if proctor not in global_proctor_slot_usage[(day, slot)]:
                                proctor_used[(day, slot)][room].add(proctor)
                                global_proctor_slot_usage[(day, slot)].add(proctor)
                                needed_proctors -= 1
                                if needed_proctors <= 0:
                                    break

                    if assigned_day is None:
                        assigned_day = day
                        assigned_slot = slot

                    remainder = col_num % max_allowed_courses
                    extra_col_start = col_num - remainder
                    for i in range(extra_col_start, col_num):
                        if i not in room_usage[(day, slot)][room]:
                            extra_columns[(day, slot)].append((room, i, row_num))

            if unassigned > 0:
                for over_room in overflow_rooms:
                    over_row_num = int(room_dimensions[over_room].split(' x ')[0])
                    over_col_num = int(room_dimensions[over_room].split(' x ')[1])

                    if available_space[(day, slot)][over_room] == 0:
                        available_space[(day, slot)][over_room] = room_size[over_room]

                    space = available_space[(day, slot)][over_room]
                    if space <= 0:
                        continue

                    assigned = False
                    for class_code, ids in enrollment_breakdown.get(course, {}).items():
                        already_assigned = assigned_students_tracker[course][class_code]
                        remaining_students = ids[already_assigned:]

                        if not remaining_students:
                            continue

                        students_to_assign = min(unassigned, len(remaining_students), space)
                        if students_to_assign == 0:
                            continue

                        assigned_ids = remaining_students[:students_to_assign]
                        assigned_students_tracker[course][class_code] += students_to_assign
                        available_space[(day, slot)][over_room] -= students_to_assign
                        unassigned -= students_to_assign

                        room_courses[(day, slot)][over_room].add(course)

                        rooms_used.append({
                            'room': over_room,
                            'columns_used': 'To be done manually',
                            'student_ids': assigned_ids,
                            'class': class_code
                        })

                        assigned = True
                        break

                    if not assigned:
                        continue

                    # Assign proctors to overflow rooms using same logic
                    needed_proctors = proctors_in_center[over_room] - len(proctor_used[(day, slot)][over_room])
                    if needed_proctors > 0:
                        # First try proctors with explicit availability
                        for proctor in proctors_with_availability:
                            if (proctor not in global_proctor_slot_usage[(day, slot)] and 
                                day in proctors_availability[proctor]):
                                proctor_used[(day, slot)][over_room].add(proctor)
                                global_proctor_slot_usage[(day, slot)].add(proctor)
                                needed_proctors -= 1
                                if needed_proctors <= 0:
                                    break
                        
                        # Then try proctors without explicit availability if still needed
                        for proctor in proctors_without_availability:
                            if proctor not in global_proctor_slot_usage[(day, slot)]:
                                proctor_used[(day, slot)][over_room].add(proctor)
                                global_proctor_slot_usage[(day, slot)].add(proctor)
                                needed_proctors -= 1
                                if needed_proctors <= 0:
                                    break

                    if assigned_day is None:
                        assigned_day = day
                        assigned_slot = slot

                    if unassigned == 0:
                        break

            if unassigned <= 0:
                break

        if course_size - unassigned > 0:
            exam_schedule.append({
                'course': course,
                'day': assigned_day,
                'slot': assigned_slot,
                'rooms': rooms_used,
                'proctors': {
                    r['room']: proctor_used[(assigned_day, assigned_slot)].get(r['room'], set()) for r in rooms_used
                }
            })
            assigned_courses.add(course)

        if unassigned > 0:
            manual_assignment_log.append({
                'course': course,
                'unassigned_count': unassigned,
                'reason': 'Not enough space in all rooms including overflow'
            })

    unassigned_column_log = []
    for (day, slot), extras in extra_columns.items():
        for room, col_index, row_num in extras:
            if room not in overflow_rooms and len(room_courses[(day, slot)][room]) >= max_courses[room]:
                continue
            unassigned_column_log.append((day, slot, room, col_index, row_num))

    return exam_schedule, manual_assignment_log, unassigned_column_log