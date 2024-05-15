from datetime import date, timedelta, datetime
from operator import itemgetter

from gitlab import Gitlab
from numpy import argmax, mean

# Set these variables to your values
gitlab_url = 'https://gitlab.com'
gitlab_private_token = ''
gitlab_group_id = 123

span_days = 365  # Time period to check
top_n = 10  # Shows top n results for categories. Change this value to your liking
min_pushes_required = 12  # Minimum number of pushes required for a user to be included in the results

# Special users sets by names
hard_included_users = {
    "Example User 1",
    "Example User 2"
}
hard_excluded_users = {
    "Example User 3",
    "Example User 4"
}

# Begin script
gl = Gitlab(gitlab_url, private_token=gitlab_private_token)

# Retrieve the GitLab group data
print(f"Retrieving '{gitlab_group_id}' group data...")
group = gl.groups.get(gitlab_group_id)

# Prepare to retrieve members of the group
print("Retrieving members from the group...")
members = group.members.list(all=True)
print(f"Retrieved {len(members)} members from the group.")

# Dictionary of users along with their average push time interval and longest period of inactivity
user_statistics = {}

# List of excluded users
excluded_users = []

# For each member in the group
for member in members:
    user = gl.users.get(member.id)

    # If user is not hard included, continue to the next user
    if user.name not in hard_included_users:
        print(f"User {user.name} is excluded from results.")
        continue

    # If user is hard excluded, continue to the next user
    if user.name in hard_excluded_users:
        print(f"User {user.name} is excluded from results.")
        continue

    # List all "pushed" events from the past year/span_days
    print(f"Retrieving events for user {user.name}...")
    events = user.events.list(
        sort="asc",
        action="pushed",
        after=str(date.today() - timedelta(days=span_days)),
        get_all=True
    )

    # If events exist and are more than the minimum required
    longest_span = None
    longest_span_dates = ["N/A", "N/A"]
    if events and len(events) >= min_pushes_required:
        # Get each "pushed" event timestamp
        timestamps = [event.created_at for event in events]
        date_objects = [
            datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            for timestamp in timestamps
        ]
        # Compute difference between consecutive timestamps
        intervals = [
            (date_objects[i + 1] - date_objects[i]).total_seconds() / 86400
            for i in range(len(date_objects) - 1)
        ]
        max_interval_index = argmax(intervals)
        longest_span = round(max(intervals), 2) if intervals else None
        longest_span_dates = (
            date_objects[max_interval_index].strftime("%m/%d"),
            date_objects[max_interval_index + 1].strftime("%m/%d"),
        )

        # Calculate average push interval
        avg_interval = round(mean(intervals), 2) if intervals else None

        # Store the user name and their stats into the dictionary
        user_statistics[user.name] = {
            "average_push_interval": avg_interval,
            "longest_span": longest_span,
            "longest_span_dates": longest_span_dates,
        }

        print(f"Average interval for user {user.name} is {user_statistics[user.name]["average_push_interval"]} days.")

    # Handle the case when there are no "pushed" events existing or not enough for a user
    elif not events or len(events) < min_pushes_required:
        print(f"User {user.name} has not made enough push events in the past {span_days} days and will be excluded from results.")

        # Add this user to the list of excluded users
        excluded_users.append(
            (
                user.name,
                longest_span if longest_span is not None else None,
                longest_span_dates if longest_span_dates is not None else ("N/A", "N/A"),
            )
        )

# Sort the dictionary by descending order of average intervals and longest span
sorted_user_statistics = dict(
    sorted(
        user_statistics.items(),
        key=lambda x: (
            x[1]["average_push_interval"] is None,
            x[1]["average_push_interval"],
            x[1]["longest_span"] is None,
            x[1]["longest_span"],
        ),
        reverse=True,
    )
)

# Prepare top n lists
avg_intervals_topn = sorted(
    [
        (user, stats["average_push_interval"])
        for user, stats in sorted_user_statistics.items()
        if stats["average_push_interval"] is not None
    ],
    key=itemgetter(1),
    reverse=True,
)[:top_n]
longest_spans_topn = sorted(
    [
        (user, stats["longest_span"], stats["longest_span_dates"])
        for user, stats in sorted_user_statistics.items()
        if stats["longest_span"] is not None
    ],
    key=itemgetter(1),
    reverse=True,
)[:top_n]

# Write top n results and result to a file
results_filename = "results.txt"
with open(results_filename, "w") as f:
    f.write(f"{group.name} Push Statistics for Last {span_days} Days\n\n")

    f.write(f"Top {top_n} Users by Average Push Interval:\n")
    for username, avg_interval in avg_intervals_topn:
        f.write(f"User: {username}, Average push interval: {avg_interval} days\n")

    f.write(f"\nTop {top_n} Users by Longest Span Without a Push:\n")
    for username, longest_span, longest_span_dates in longest_spans_topn:
        f.write(f"User: {username}, Longest span without a push: {longest_span} days, from {longest_span_dates[0]} to {longest_span_dates[1]}\n")

    f.write("\nAll Users Included in the Results:\n")
    for username, stats in sorted_user_statistics.items():
        if stats["average_push_interval"] is not None:
            f.write(f"User: {username}, Average push interval: {stats["average_push_interval"]} days, Longest span without a push: {stats["longest_span"]} days, from {stats["longest_span_dates"][0]} to {stats["longest_span_dates"][1]}\n")

    # Write the excluded users to the file
    if len(excluded_users) > 0:
        f.write(f"\nList of Users Who Made Less Than {min_pushes_required} Push Events:\n")

    for username, longest_span, longest_span_dates in excluded_users:
        if longest_span is not None:
            f.write(f"User: {username}, Longest span without a push: {longest_span} days, from {longest_span_dates[0]} to {longest_span_dates[1]}\n")
        else:
            f.write(f"User: {username}\n")

print(f"Results have been written to {results_filename}.")
