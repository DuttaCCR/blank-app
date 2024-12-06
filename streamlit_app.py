import streamlit as st
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# import atexit
from streamlit_dynamic_filters import DynamicFilters

# Function to trigger a refresh by modifying a session state variable
def trigger_refresh():
    if "refresh" not in st.session_state:
        st.session_state["refresh"] = 0
    st.session_state["refresh"] += 1

# Watchdog Event Handler
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, app_callback):
        super().__init__()
        self.app_callback = app_callback

    def on_created(self, event):
        if event.src_path.endswith(".sav"):  # Trigger on new .sav files
            self.app_callback()

    def on_modified(self, event):
        if event.src_path.endswith(".sav"):  # Trigger on modified .sav files
            self.app_callback()

# Function to start Watchdog in a separate thread
def start_watchdog(directory, callback):
    event_handler = FileChangeHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    return observer

# Streamlit App
# st.header("How did you originally become aware of ROXOR?")

# # Directory to watch
# current_directory = os.path.dirname(os.path.abspath(__file__))  # Current script's directory
# watch_directory = os.path.join(current_directory, "Quarters")  # Path to "Quarters" folder

# Get the current script's directory
current_directory = Path(__file__).resolve().parent
watch_directory = current_directory / "Quarters"

# Start Watchdog
if "watchdog_started" not in st.session_state:
    observer = start_watchdog(watch_directory, trigger_refresh)
    st.session_state.watchdog_started = True

# Function to load all .sav files dynamically
def load_all_sav_files(directory):
    # Convert the directory to a Path object
    directory = Path(directory)
    
    # Find all .sav files in the directory
    sav_files = list(directory.glob("*.sav"))
    
    dataframes = []
    for file in sav_files:
        try:
            # Load .sav file into a DataFrame
            df = pd.read_spss(file)
            
            # Add a column to track the file source
            df['source_file'] = file.name  # file.name gives the basename of the file
            
            # Append the DataFrame to the list
            dataframes.append(df)
        except Exception as e:
            st.warning(f"Error loading file {file}: {e}")
    
    # Concatenate all DataFrames if any are loaded; otherwise return an empty DataFrame
    return pd.concat(dataframes) if dataframes else pd.DataFrame()

# Load all .sav files
df = load_all_sav_files(watch_directory)

if df.empty:
    st.write("No data available to display.")
else:
# -------------------------------------------------------------------------------------------------------------
    st.set_page_config(
    page_title="Mahindra Report",
    page_icon="📊",
    )

    st.markdown(
    """
    <style>
    .main {
        max-width: 1200px; /* Set a maximum width */
        margin: 0 auto;    /* Center align */
    }

    .center-title {
        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True,
    )

    # Use the custom CSS class
    st.markdown("<h1 class='center-title'>ROXOR</h1>", unsafe_allow_html=True)
    st.markdown("<h1 class='center-title'>60-Day Satisfaction</h1>", unsafe_allow_html=True)
    st.markdown("<h1 class='center-title'>November 2024</h1>", unsafe_allow_html=True)

    st.title("")

    st.header("How did you originally become aware of ROXOR?")

    # Filter out rows where Q1 equals 'DNU'
    # filtered_df = df[df['Q1'] != 'DNU']
    df['Q25'] = df['Q25'].replace('', "High school or less")  # Replace empty strings with 0
    df['Q25'] = df['Q25'].fillna("High school or less")  
    # df['Q25'] = pd.to_numeric(df['Q25'])

    df.rename(
    columns={
        "Q20A": "Gender",
        "Q21": "Marital Status",
        "Q23": "Number of People in Household",
        "Q24": "Highest Level of Education",
        "Q25": "Graduated with..."
    },
    inplace=True  # Modify the DataFrame in place
)

    dynamic_filters = DynamicFilters(df, filters=["Gender", "Marital Status", "Number of People in Household", "Highest Level of Education", "Graduated with..."])

    with st.sidebar:
        st.write("Apply filters in any order")

    dynamic_filters.display_filters(location='sidebar')

    # dynamic_filters.display_df()

    filtered_df = dynamic_filters.filter_df()

    # Group and calculate percentages on the filtered DataFrame
    category_counts = filtered_df.groupby(['Q1', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = ['All other', 'Previous ownership, experience, knowledge', 'Article in trade magazine', 'Research, shopping', 'Sponsorship of event', 'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', 'Dealer signage and displayed product', 'Advertisements (TV, Print, Radio or Web)']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(title="Source File")

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)

# -------------------------------------------------------------------------------------------------------------


    st.header("How would you rate your overall satisfaction with your ROXOR?")

    # Group and calculate percentages on the filtered DataFrame
    category_counts = filtered_df.groupby(['Q2', 'source_file']).size().unstack(fill_value=0)

    # filtered_df = df[df['Q1'] != 'DNU']


    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = ['1 (Very Dissatisfied)', '2', '3', '4', '5', '6', '7', '8', '9', '10 (Very Satisfied)']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(title="Source File")

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)

# # -------------------------------------------------------------------------------------------------------------


    st.header("How would you rate your overall satisfaction with your ROXOR?")
    
    import matplotlib.pyplot as plt
    import streamlit as st

    # Filter the DataFrame for ratings of '8', '9', or '10 (Very Satisfied)'
    filtered_ratings = df[df['Q2'].isin(['8', '9', '10 (Very Satisfied)'])]

    # Group by 'source_file' and sum the counts
    ratings_sum = filtered_ratings.groupby('source_file').size()

    # Calculate the total number of all ratings
    total_ratings_count = df.groupby('source_file').size()

    # Calculate percentages: proportion of '8', '9', '10 (Very Satisfied)' to all ratings
    ratings_percentages = (ratings_sum / total_ratings_count) * 100

    # Rename the bar labels (custom mapping)
    label_mapping = {
        'source_file_3': 'Label 3',
        'source_file_2': 'Label 2',
        'source_file_1': 'Label 1',
    }
    ratings_sum.rename(index=label_mapping, inplace=True)
    ratings_percentages.rename(index=label_mapping, inplace=True)

    # Plot the horizontal bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.barh(ratings_sum.index, ratings_sum, color='skyblue')

    # Add percentages at the end of each bar
    for bar, percentage in zip(bars, ratings_percentages):
        plt.text(
            bar.get_width() + 1,  # Slightly beyond the bar's end
            bar.get_y() + bar.get_height() / 2,  # Centered vertically
            f'{percentage:.1f}%',  # Format as percentage
            va='center',  # Vertical alignment
            ha='left'  # Horizontal alignment
        )

    # Add labels and title
    # plt.xlabel([])
    # plt.ylabel('Source File')
    plt.xticks(
        []
    )
    plt.title('Sum of Ratings of 8, 9, or 10 – Extremely Satisfied')
    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)





    # Map the ratings to numeric values
    rating_mapping = {
        '1 (Very Dissatisfied)': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
        '7': 7,
        '8': 8,
        '9': 9,
        '10 (Very Satisfied)': 10
    }
    df['Q2_numeric'] = df['Q2'].map(rating_mapping)

    # Group by 'source_file' and calculate the average rating
    average_ratings = df.groupby('source_file')['Q2_numeric'].mean()

    # Rename the bar labels (custom mapping)
    label_mapping = {
        'source_file_1': 'Label 1',
        'source_file_2': 'Label 2',
        'source_file_3': 'Label 3'
    }
    average_ratings.rename(index=label_mapping, inplace=True)

    # Plot the horizontal bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.barh(average_ratings.index, average_ratings, color='lightgreen')

    # Add average rating values at the end of each bar
    for bar, avg in zip(bars, average_ratings):
        plt.text(
            bar.get_width() + 0.1,  # Slightly beyond the bar's end
            bar.get_y() + bar.get_height() / 2,  # Centered vertically
            f'{avg:.2f}',  # Format with 2 decimal places
            va='center',  # Vertical alignment
            ha='left'  # Horizontal alignment
        )

    # Add labels and title
    # plt.xlabel('Average Rating')
    # plt.ylabel('Source File')
    plt.title('Average Ratings')
    plt.tight_layout()

    # Show the plot in Streamlit
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    plt.xticks(
        []
    )
    st.pyplot(plt)


# # -------------------------------------------------------------------------------------------------------------

    
    
    st.header("")
    st.header("Have you had any issues with product or performance quality?")
    

    # Filter for 'Yes' responses in Q4a
    yes_responses = df[df['Q4A'] == 'Yes']

    # Count the number of 'Yes' responses for each source file
    yes_counts = yes_responses.groupby('source_file').size()

    # Calculate the total responses for each source file
    total_counts = df.groupby('source_file').size()

    # Calculate the percentage of 'Yes' responses
    yes_percentages = (yes_counts / total_counts) * 100

    # Rename the bar labels (custom mapping)
    label_mapping = {
        'hw': 'Label 1',
        'source_file_2': 'Label 2',
        'source_file_3': 'Label 3'
    }
    yes_percentages.rename(index=label_mapping, inplace=True)

    # Plot the horizontal bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.barh(yes_percentages.index, yes_percentages, color='skyblue')

    # Add percentages at the end of each bar
    for bar, percentage in zip(bars, yes_percentages):
        plt.text(
            bar.get_width() + 1,  # Slightly beyond the bar's end
            bar.get_y() + bar.get_height() / 2,  # Centered vertically
            f'{percentage:.1f}%',  # Format as percentage
            va='center',  # Vertical alignment
            ha='left'  # Horizontal alignment
        )

    # Add labels and title
    # plt.xlabel('Percentage of Yes Responses (%)')
    # plt.ylabel('Source File')
    # plt.title('Percentage of Yes Responses for Q4a by Source File')
    plt.tight_layout()
    plt.xticks(
        []
    )
    # Show the plot in Streamlit
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)


# # -------------------------------------------------------------------------------------------------------------

    st.header("")
    st.header("How likely would you be to recommend ROXOR to a friend or colleague?")


    # Group and calculate percentages on the filtered DataFrame
    category_counts = filtered_df.groupby(['Q5', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

    # Define your custom order for the categories
    custom_order = ['1 (Definitely Would Not Recommend)', '2', '3', '4', '5', '6', '7', '8', '9', '10 (Definitely Would Recommend)']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Combine '1', '2', '3', '4', '5' into a single category '5 or less'
    category_percentages.loc['5 or less'] = category_percentages.loc['1 (Definitely Would Not Recommend)':'5'].sum(axis=0)

    # Drop the original '1', '2', '3', '4', '5' categories after aggregating them
    category_percentages.drop(['1 (Definitely Would Not Recommend)', '2', '3', '4', '5'], inplace=True)

    # Reorder to ensure '5 or less' is at the bottom and then 6, 7, 8, 9, 10 follow
    category_percentages = category_percentages.loc[['5 or less', '6', '7', '8', '9', '10 (Definitely Would Recommend)']]

    # Plotting the clustered bar chart with the aggregated "5 or less" category at the bottom
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    # Plot each file as a separate bar group
    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',  # Display percentage
                va='center',
                ha='left'
            )

    # Add labels and title
    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('Dynamic Clustered Bar Chart for Q5 (Including Aggregated "5 or less")')

    # Adjust y-ticks to show categories including the aggregated one
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )

    # Add a legend
    plt.legend(title="Source File")

    # Tight layout for the plot
    plt.tight_layout()

    # Show the plot in Streamlit
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)





# # -------------------------------------------------------------------------------------------------------------


    st.header("INSERT How likely would you be to recommend ROXOR to a friend or colleague?")

    # Example DataFrame for testing; replace with your actual filtered_df
    # filtered_df = pd.DataFrame(...)  

    # Define the ratings we are interested in (8, 9, 10)
    ratings_of_interest = ['8', '9', '10 (Definitely Would Recommend)']

    try:
        # Group and calculate counts for each rating and source file
        category_counts = filtered_df.groupby(['Q5', 'source_file']).size().unstack(fill_value=0)

        # Ensure all ratings of interest are in the index by reindexing
        # category_counts = category_counts.reindex(ratings_of_interest, fill_value=0)

        # Calculate the total counts for all ratings across source files
        total_counts = category_counts.sum(axis=0)

        # Sum the counts for ratings of interest (8, 9, 10)
        sum_counts_of_interest = category_counts.loc[ratings_of_interest].sum(axis=0)

        # Calculate the percentage of the total represented by ratings 8, 9, and 10
        percentage_of_total = (sum_counts_of_interest / total_counts) * 100

        # Replace NaN values resulting from division with 0 (e.g., if total_counts is 0)
        percentage_of_total = percentage_of_total.fillna(0)

        # Create the bar chart
        plt.figure(figsize=(12, 8))
        bars = plt.barh(ratings_of_interest, percentage_of_total, color='skyblue')

        # Add percentages at the end of each bar
        for bar, rating in zip(bars, ratings_of_interest):
            bar_height = bar.get_width()
            plt.text(
                bar_height + 0.5,  # Slightly beyond the bar's end
                bar.get_y() + bar.get_height() / 2,  # Centered vertically
                f'{bar_height:.1f}%' if total_counts.sum() > 0 else '0%',  # Show 0% if no data
                va='center',  # Vertical alignment
                ha='left'  # Horizontal alignment
            )

        # Add labels and title
        plt.title('Percentage of "Definitely Would Recommend" Responses (8, 9, 10)')
        plt.xlabel('Percentage')
        plt.ylabel('Ratings')
        plt.tight_layout()

        # Style the axes
        plt.xticks([])
        ax = plt.gca()
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)
        ax.spines['bottom'].set_visible(False)

        # Display the chart
        st.pyplot(plt)

    except Exception as e:
        st.text(f"Error: {e}")






# # -------------------------------------------------------------------------------------------------------------

    st.header("")
    st.header("What is your primary use of your new ROXOR?")

     # Group and calculate percentages on the filtered DataFrame
    category_counts = filtered_df.groupby(['Q7', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = [
        'Public Sector/Government',
        'Commercial use (landscaping, mowing highways, construction, etc)',
        'Income producing agricultural use such as farming or ranching',
        'Rural Lifestyle such as hobby farming or recreational'
    ]

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(
        title="Source File",  # Title of the legend
        loc="upper left",     # Location relative to the axes
        bbox_to_anchor=(1.0, 0)  # Place it fully outside the plot to the right
    )

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)

# # -------------------------------------------------------------------------------------------------------------

    # st.header("")
    # st.header("What are the primary reasons you choose ROXOR over other brands you considered?")
    # directory_path = 'Quarters'  # Change this if needed

    # # Get the list of files in the directory
    # file_list = sorted(os.listdir(directory_path))

    # # Select the first file in the directory
    # first_file = os.path.join(directory_path, file_list[0])

    # # Load the first file into a DataFrame (assuming it's an SPSS file)
    # firstFile = pd.read_spss(first_file)

    # # Define the Q9 columns
    # q9_columns = ['Q9_1', 'Q9_2', 'Q9_3', 'Q9_4', 'Q9_5', 'Q9_6', 'Q9_7', 'Q9_8', 'Q9_9', 'Q9_10', 'Q9_11', 'Q9_12', 'Q9_13', 'Q9_14', 'Q9_15']

    # # Map the Q9 columns to descriptive labels
    # q9_labels = {
    #     'Q9_15': "Other Mention",
    #     'Q9_14': "Special offers and Promotions",
    #     'Q9_13': "Current Mahindra Owner",
    #     'Q9_12': "Recommendation",
    #     'Q9_11': "Financing",
    #     'Q9_10': "Brand Reputation",
    #     'Q9_9': "Online Research",
    #     'Q9_8': "Dealer Reputation",
    #     'Q9_7': "Availability of Services and Parts",
    #     'Q9_6': "Performance",
    #     'Q9_5': "Easy to Operate and Maintain",
    #     'Q9_4': "Good Value",
    #     'Q9_3': "Warranty Offered",
    #     'Q9_2': "Price",
    #     'Q9_1': "Product Features",
    # }

    # # Check if these columns exist in the dataframe
    # q9_columns = [col for col in q9_columns if col in firstFile.columns]

    # # Calculate the percentage of "Checked" in each column, based on non-null values
    # checked_percentages = firstFile[q9_columns].apply(
    #     lambda col: (col.str.contains('Checked').sum() / col.notna().sum()) * 100
    # )



    # # Replace column names with descriptive labels for the plot
    # checked_percentages.index = [q9_labels.get(col, col) for col in checked_percentages.index]

    # # custom_order = [
    # #     "Other Mention",
    # #     "Financing",
    # #     "Dealer Reputation",
    # #     "Availability of Services and Parts",
    # #     "Current Mahindra Owner",
    # #     "Special offers and Promotions",
    # #     "Online Research",
    # #     "Recommendation",
    # #     "Brand Reputation",
    # #     "Warranty Offered",
    # #     "Easy to Operate and Maintain",
    # #     "Performance",
    # #     "Good Value",
    # #     "Product Features"
    # #     "Price",
    # #     ]

    # # # Ensure the categories are in the custom order
    # # checked_percentages = checked_percentages.reindex(custom_order)

    # # Plot the bar chart for frequency of 'Checked' responses (as percentage of total rows)
    # plt.figure(figsize=(12, 8))
    # bars = plt.barh(checked_percentages.index, checked_percentages, color='skyblue')

    # # Add frequency count (percentage) at the end of each bar
    # for bar in bars:
    #     plt.text(
    #         bar.get_width() + 0.1,  # Slightly beyond the bar's end
    #         bar.get_y() + bar.get_height() / 2,  # Centered vertically
    #         f'{bar.get_width():.1f}%',  # Frequency as percentage
    #         va='center',  # Vertical alignment
    #         ha='left'  # Horizontal alignment
    #     )

    # # Add labels and title
    # plt.xlabel('Percentage of "Checked" Responses')
    # plt.ylabel('Survey Question')
    # plt.title('Percentage of "Checked" Responses for Q9_1 to Q9_15')

    # # Rotate x-axis labels for better readability
    # plt.tight_layout()

    # # Show the plot in Streamlit
    # ax = plt.gca()  # Get current axes
    # ax.grid(False)  # Turn off all gridlines
    # ax.spines['top'].set_visible(False)  # Hide the top spine
    # ax.spines['right'].set_visible(False)  # Hide the right spine
    # ax.spines['left'].set_visible(True)  # Hide the left spine
    # ax.spines['bottom'].set_visible(False)  # Hide the left spine
    # st.pyplot(plt)

# # --------------------------------------------------------------------------------------------------------------------

    # st.header("Importance Comparison (Top 2 Box Scoring)")

    # # Directory to watch
    # # current_directory = os.path.dirname(os.path.abspath(__file__))  # Current script's directory
    # # watch_directory = os.path.join(current_directory, "Quarters")  # Path to "Quarters" folder

    # # Start Watchdog (If needed)
    # if "watchdog_started" not in st.session_state:
    #     observer = start_watchdog(watch_directory, trigger_refresh)
    #     st.session_state.watchdog_started = True

    # # Function to load all .sav files dynamically
    # def load_all_sav_files(directory):
    #     sav_files = glob.glob(os.path.join(directory, "*.sav"))  # Find all .sav files in the "Quarters" folder
    #     dataframes = []
    #     for file in sav_files:
    #         try:
    #             df = pd.read_spss(file)
    #             df['source_file'] = os.path.basename(file)  # Add a column to track the file source
    #             dataframes.append(df)
    #         except Exception as e:
    #             st.warning(f"Error loading file {file}: {e}")
    #     return pd.concat(dataframes) if dataframes else pd.DataFrame()

    # # Load all .sav files
    # df = load_all_sav_files(watch_directory)

    # # List of all relevant columns
    # columns_to_check = [
    #     'Q10Q11_r1_c1', 'Q10Q11_r2_c1', 'Q10Q11_r3_c1', 'Q10Q11_r4_c1', 'Q10Q11_r5_c1', 'Q10Q11_r6_c1', 
    #     'Q10Q11_r7_c1', 'Q10Q11_r8_c1', 'Q10Q11_r9_c1', 'Q10Q11_r1_c2', 'Q10Q11_r2_c2', 'Q10Q11_r3_c2', 
    #     'Q10Q11_r4_c2', 'Q10Q11_r5_c2', 'Q10Q11_r6_c2', 'Q10Q11_r7_c2', 'Q10Q11_r8_c2', 'Q10Q11_r9_c2'
    # ]

    # # Corresponding titles for each column
    # column_titles = {
    #     'Q10Q11_r1_c1': "10. How important is the overall reputation of the dealer?",
    #     'Q10Q11_r2_c1': "10. How important is the salesperson's knowledge about your Roxor and its features?",
    #     'Q10Q11_r3_c1': "10. How important is the salesperson's ability to answer your questions?",
    #     'Q10Q11_r4_c1': "10. How important is the dealer has a variety of models to view prior to purchase?",
    #     'Q10Q11_r5_c1': "10. How important is the dealer is conveniently located?",
    #     'Q10Q11_r6_c1': "10. How important is the the availability and responsiveness of the dealer?",
    #     'Q10Q11_r7_c1': "10. How important is your Roxor is delivered in a timely manner?",
    #     'Q10Q11_r8_c1': "10. How important is dealer service and support capability?",
    #     'Q10Q11_r9_c1': "10. How important is cleanliness and layout of dealership?",
    #     'Q10Q11_r1_c2': "11. How would you rate your dealer on the overall reputation of the dealer?",
    #     'Q10Q11_r2_c2': "11. How would you rate your dealer on the salesperson's knowledge about your Roxor and its features?",
    #     'Q10Q11_r3_c2': "11. How would you rate your dealer on the salesperson's ability to answer your questions?",
    #     'Q10Q11_r4_c2': "11. How would you rate your dealer on the dealer has a variety of models to view prior to purchase?",
    #     'Q10Q11_r5_c2': "11. How would you rate your dealer on the dealer is conveniently located?",
    #     'Q10Q11_r6_c2': "11. How would you rate your dealer on the the availability and responsiveness of the dealer?",
    #     'Q10Q11_r7_c2': "11. How would you rate your dealer on your Roxor was delivered in a timely manner?",
    #     'Q10Q11_r8_c2': "11. How would you rate your dealer on dealer service and support capability?",
    #     'Q10Q11_r9_c2': "11. How would you rate your dealer on cleanliness and layout of dealership?"
    # }

    # # Loop over each column and create a bar chart for it
    # for idx, col in enumerate(columns_to_check):
    #     if col in df.columns:
    #         # Determine the response to count based on index
    #         response_to_count = "10 (Extremely Important)" if idx < len(columns_to_check) // 2 else "10 (Excellent)"
            
    #         # Filter out "Don't know" responses for this column
    #         filtered_df = df[df[col] != "Don't know"]
            
    #         # Count the occurrences of the target response and '9'
    #         filtered_df[f'checked_{col}'] = filtered_df[col].apply(lambda x: 1 if str(x) in [response_to_count, '9'] else 0)
            
    #         # Group by the source file and calculate the sum of 'checked' values for each file
    #         file_counts = filtered_df.groupby('source_file')[f'checked_{col}'].sum().reset_index(name='checked_sum')
            
    #         # Calculate the total number of valid responses for each file
    #         total_counts = filtered_df.groupby('source_file')[col].count().reset_index(name='total_count')
            
    #         # Merge the file counts with total counts
    #         file_counts = pd.merge(file_counts, total_counts, on='source_file')
            
    #         # Calculate the percentage of the target responses relative to total responses
    #         file_counts['percentage'] = (file_counts['checked_sum'] / file_counts['total_count']) * 100

    #         # Plot the bar chart for the percentage of the target responses
    #         fig, ax = plt.subplots(figsize=(12, 8))
    #         bars = ax.bar(file_counts['source_file'], file_counts['percentage'], color='skyblue')

    #         # Add percentage value at the top of each bar
    #         for bar in bars:
    #             ax.text(
    #                 bar.get_x() + bar.get_width() / 2,  # Center the text horizontally
    #                 bar.get_height() + 0.1,  # Slightly above the bar
    #                 f'{bar.get_height():.1f}%',  # Percentage
    #                 ha='center',  # Horizontal alignment
    #                 va='bottom'  # Vertical alignment
    #             )

    #         # Set labels and title for each column using the custom title mapping
    #         ax.set_xlabel('Source File')
    #         ax.set_ylabel(f'Percentage of "9" and "{response_to_count}"')
    #         ax.set_title(column_titles.get(col, f"Percentage of '9' and '{response_to_count}' for {col}"))
            
    #         # Rotate x-axis labels for readability
    #         plt.xticks(rotation=90)

    #         # Show the plot in Streamlit
    #         st.pyplot(fig)
            



# # --------------------------------------------------------------------------------------------------------------------

    st.header("Overall, how satisfied are you with your dealer experience?")


    # Group and calculate percentages on the filtered DataFrame
    category_counts = filtered_df.groupby(['Q12', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

    # Define your custom order for the categories
    custom_order = ['1 (Very Dissatisfied)', '2', '3', '4', '5', '6', '7', '8', '9', '10 (Very Satisfied)']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Combine '1', '2', '3', '4', '5' into a single category '5 or less'
    category_percentages.loc['5 or less'] = category_percentages.loc['1 (Very Dissatisfied)':'5'].sum(axis=0)

    # Drop the original '1', '2', '3', '4', '5' categories after aggregating them
    category_percentages.drop(['1 (Very Dissatisfied)', '2', '3', '4', '5'], inplace=True)

    # Reorder to ensure '5 or less' is at the bottom and then 6, 7, 8, 9, 10 follow
    category_percentages = category_percentages.loc[['5 or less', '6', '7', '8', '9', '10 (Very Satisfied)']]

    # Plotting the clustered bar chart with the aggregated "5 or less" category at the bottom
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    # Plot each file as a separate bar group
    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',  # Display percentage
                va='center',
                ha='left'
            )

    # Add labels and title
    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('Dynamic Clustered Bar Chart for Q5 (Including Aggregated "5 or less")')

    # Adjust y-ticks to show categories including the aggregated one
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )

    # Add a legend
    plt.legend(title="Source File")

    # Tight layout for the plot
    plt.tight_layout()

    # Show the plot in Streamlit
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)


# # --------------------------------------------------------------------------------------------------------------------
    st.header("")
    st.header("Overall, how satisfied are you with your dealer experience?")

    # Check if Q12 column exists
    if 'Q12' in df.columns:
        # Filter valid responses and exclude "Don't know"
        valid_responses = ['8', '9', '10 (Very Satisfied)']
        excluded_responses = ["Don't know"]

        # Create a column to identify valid responses
        df['Q12_valid'] = df['Q12'].apply(lambda x: 1 if str(x).strip() in valid_responses else 0)

        # Create a column to exclude "Don't know" from the total
        df['Q12_in_total'] = df['Q12'].apply(lambda x: 0 if str(x).strip() in excluded_responses else 1)

        # Group by source file and calculate sums of valid responses and total responses
        file_sums = df.groupby('source_file').agg(
            valid_responses_sum=('Q12_valid', 'sum'),
            total_responses=('Q12_in_total', 'sum')
        ).reset_index()

        # Calculate percentages
        file_sums['percentage'] = (file_sums['valid_responses_sum'] / file_sums['total_responses']) * 100

        # Create a horizontal bar chart
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(file_sums['source_file'], file_sums['percentage'], color='skyblue')

        # Add percentage values to the right of each bar
        for bar in bars:
            ax.text(
                bar.get_width() + 1,  # Position slightly beyond the bar's width
                bar.get_y() + bar.get_height() / 2,  # Centered vertically
                f'{bar.get_width():.1f}%',  # Display percentage
                va='center',  # Vertical alignment
                ha='left'  # Horizontal alignment
            )

        # Set chart labels and title
        ax.set_xlabel('Percentage of Valid Responses (%)')
        ax.set_ylabel('Source File')
        ax.set_title('Percentage of Valid Responses for Q12: 8, 9, and 10 (Very Satisfied)')
        
        # Show the plot in Streamlit
        st.pyplot(fig)

    else:
        st.warning("The column 'Q12' is not present in the loaded data.")

    st.header("Overall, how satisfied are you with your dealer experience?")

        # Check if Q12 column exists
    if 'Q12' in df.columns:
        # Map all valid responses to numerical values
        response_mapping = {
            '1 (Very Dissatisfied)': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5,
            '6': 6,
            '7': 7,
            '8': 8,
            '9': 9,
            '10 (Very Satisfied)': 10
        }

        excluded_responses = ["Don't know"]

        # Create a column with numerical values or NaN for invalid/excluded responses
        df['Q12_numeric'] = df['Q12'].apply(lambda x: response_mapping.get(str(x).strip(), None) if str(x).strip() not in excluded_responses else None)

        # Group by source file and calculate the mean of numerical responses
        file_means = df.groupby('source_file')['Q12_numeric'].mean().reset_index(name='mean_value')

        # Create a horizontal bar chart
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(file_means['source_file'], file_means['mean_value'], color='skyblue')

        # Add mean values to the right of each bar
        for bar in bars:
            ax.text(
                bar.get_width() + 0.1,  # Position slightly beyond the bar's width
                bar.get_y() + bar.get_height() / 2,  # Centered vertically
                f'{bar.get_width():.2f}',  # Display mean value
                va='center',  # Vertical alignment
                ha='left'  # Horizontal alignment
            )

        # Set chart labels and title
        ax.set_xlabel('Mean Value of Responses')
        ax.set_ylabel('Source File')
        ax.set_title('Mean Value of Responses for Q12')
        
        # Show the plot in Streamlit
        st.pyplot(fig)

    else:
        st.warning("The column 'Q12' is not present in the loaded data.")



# --------------------------------------------------------------------------------------------------------------------

    # st.header("")
    # st.header("INSERT Since purchasing your ROXOR, have you visited the dealer for any of the following reasons?")
    

    # # # Assuming 'df' is already loaded with your data
    # # columns_to_include = [
    # #     'Q16_1', 'Q16_2', 'Q16_3', 'Q16_4', 'Q16_5',
    # #     'Q16_6', 'Q16_7', 'Q16_8', 'Q16_7_other'
    # # ]

    # # Convert "Checked" to 1 and "Unchecked" to 0 for the Q16_1 column
    # df['checked_Q16_1'] = df['Q16_1'].apply(lambda x: 1 if str(x) == 'Checked' else 0)

    # # Group by source_file and calculate the sum of "Checked" responses for Q16_1 in each file
    # checked_counts = df.groupby('source_file')['checked_Q16_1'].sum()

    # # Plot the bar chart
    # fig, ax = plt.subplots(figsize=(10, 6))
    # checked_counts.plot(kind='bar', ax=ax, color='skyblue')

    # # Set the title and labels
    # ax.set_title('Frequency of "Checked" Responses for Q16_1 Across Files')
    # ax.set_xlabel('Source File')
    # ax.set_ylabel('Number of "Checked" Responses')

    # # Show the count on top of each bar
    # for i, v in enumerate(checked_counts):
    #     ax.text(i, v + 0.1, str(v), ha='center', va='bottom')

    # # Rotate x-axis labels for readability
    # plt.xticks(rotation=45, ha='right')

    # # Adjust layout for better visibility
    # plt.tight_layout()

    # # Show the plot in your Streamlit app
    # st.pyplot(fig)


# --------------------------------------------------------------------------------------------------------------------
    st.header("")
    st.header("Please rate your dealer experience when returning to the dealer. Would you say it was a(n) [_____] experience?")
        # Filter out rows where Q1 equals 'DNU'
    filtered_df = df[df['Q18'] != 'Don’t Know']

    # Group and calculate percentages on the filtered DataFrame
    category_counts = filtered_df.groupby(['Q18', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = ['Poor', 'Fair', 'Neutral', 'Good', 'Excellent']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(title="Source File")

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)



# --------------------------------------------------------------------------------------------------------------------
    st.header("")
    st.header("Gender")
    # Group and calculate percentages on the filtered DataFrame
    category_counts = filtered_df.groupby(['Q20A', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = ['Female', 'Male']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(title="Source File")

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)

# --------------------------------------------------------------------------------------------------------------------
    st.header("")
    st.header("Age")
        
    filtered_df = df[df['QD'] != 'Prefer not to answer']
    category_counts = filtered_df.groupby(['QD', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = ['75 or older', '65 - 74', '55 - 64', '45 - 54', '35 - 44', '25 - 34', '18 - 24']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(title="Source File")

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)

# --------------------------------------------------------------------------------------------------------------------
    st.header("")
    st.header("Ethnicity")
        
    filtered_df = df[df['QE'] != 'Prefer not to answer']
    category_counts = filtered_df.groupby(['QE', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = ['Prefer not to answer', 'Other', 'Hispanic', 'Asian', 'African American or Black', 'Caucasian or White']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(title="Source File")

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)

# --------------------------------------------------------------------------------------------------------------------
    st.header("")
    st.header("Marital Status")
        
    filtered_df = df[df['Q21'] != 'Prefer not to answer']
    category_counts = filtered_df.groupby(['Q21', 'source_file']).size().unstack(fill_value=0)

    # Calculate percentages for each source file
    category_percentages = category_counts.div(category_counts.sum(axis=0), axis=1) * 100

        # Define your custom order for the categories'Saw a floor model at a show', 'Online', 'Friend or family member recommended them', , 'Saw a floor model at a show'
    custom_order = ['Refused', 'Other', 'Widowed', 'Divorced', 'Single', 'Married']

    # Ensure the categories are in the custom order
    category_percentages = category_percentages.reindex(custom_order)

    # Plotting the clustered bar chart with custom order
    plt.figure(figsize=(12, 8))
    width = 0.2  # Adjust bar width for multiple files
    positions = list(range(len(category_percentages.index)))

    for i, col in enumerate(category_percentages.columns):
        bars = plt.barh(
            [pos + i * width for pos in positions],
            category_percentages[col],
            height=width,
            label=col
        )
        for bar in bars:
            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.1f}%',
                va='center',
                ha='left'
            )

    plt.xticks(
        []
    )
    plt.ylabel('')
    plt.title('')
    plt.yticks(
        [pos + (width * len(category_percentages.columns)) / 2 for pos in positions],
        category_percentages.index
    )
    plt.legend(title="Source File")

    plt.tight_layout()
    ax = plt.gca()  # Get current axes
    ax.grid(False)  # Turn off all gridlines
    ax.spines['top'].set_visible(False)  # Hide the top spine
    ax.spines['right'].set_visible(False)  # Hide the right spine
    ax.spines['left'].set_visible(True)  # Hide the left spine
    ax.spines['bottom'].set_visible(False)  # Hide the left spine
    st.pyplot(plt)


# # Register cleanup for when the app stops
# @atexit.register
# def cleanup():
#     if "watchdog_started" in st.session_state:
#         observer.stop()
#         observer.join()
#         del st.session_state.watchdog_started
