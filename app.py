import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Personal CRM", page_icon="📊", layout="wide")

DATA_FILE = "contacts_data.json"
LISTS_FILE = "lists_data.json"

def load_lists():
    if os.path.exists(LISTS_FILE):
        with open(LISTS_FILE, 'r') as f:
            return json.load(f)
    return {"Default": {"name": "Default", "color": "#1f77b4", "description": "Default contact list"}}

def save_lists(lists_data):
    with open(LISTS_FILE, 'w') as f:
        json.dump(lists_data, f, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        # Add List column if it doesn't exist
        if 'List' not in df.columns:
            df['List'] = 'Default'
        return df
    return pd.DataFrame(columns=['Business', 'Name', 'Number', 'Email', 'Location', 'Industry', 'Call Notes', 'Date Added', 'List'])

def save_data(df):
    data = df.to_dict('records')
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    st.title("📊 Personal CRM")

    # Initialize session state
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
    if 'current_list' not in st.session_state:
        st.session_state.current_list = 'Default'

    df = load_data()
    lists_data = load_lists()

    # List management section
    st.subheader("📋 Manage Lists")
    col1, col2 = st.columns([2, 1])

    with col1:
        # Current list selector
        list_options = list(lists_data.keys())
        if st.session_state.current_list not in list_options:
            st.session_state.current_list = 'Default'

        selected_list = st.selectbox(
            "Select Active List:",
            list_options,
            index=list_options.index(st.session_state.current_list),
            key="list_selector"
        )
        st.session_state.current_list = selected_list

        # Display current list info
        current_list_info = lists_data[selected_list]
        st.markdown(f"**{current_list_info['name']}** - {current_list_info.get('description', '')}")

    with col2:
        if st.button("➕ New List"):
            st.session_state.show_new_list_form = True
        if st.button("⚙️ Edit Lists"):
            st.session_state.show_edit_lists = True

    # New list form
    if st.session_state.get('show_new_list_form', False):
        with st.form("new_list_form"):
            st.subheader("Create New List")
            new_list_name = st.text_input("List Name")
            new_list_description = st.text_input("Description (optional)")
            new_list_color = st.color_picker("List Color", "#1f77b4")

            col1, col2 = st.columns(2)
            with col1:
                create_list = st.form_submit_button("Create List")
            with col2:
                cancel_list = st.form_submit_button("Cancel")

            if create_list and new_list_name:
                if new_list_name not in lists_data:
                    lists_data[new_list_name] = {
                        "name": new_list_name,
                        "description": new_list_description,
                        "color": new_list_color
                    }
                    save_lists(lists_data)
                    st.session_state.current_list = new_list_name
                    st.session_state.show_new_list_form = False
                    st.success(f"List '{new_list_name}' created!")
                    st.rerun()
                else:
                    st.error("A list with this name already exists!")

            if cancel_list:
                st.session_state.show_new_list_form = False
                st.rerun()

    # Edit lists form
    if st.session_state.get('show_edit_lists', False):
        st.subheader("Edit Lists")
        for list_name, list_info in lists_data.items():
            if list_name != 'Default':  # Don't allow deleting default list
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{list_info['name']}** - {list_info.get('description', '')}")
                with col2:
                    if st.button(f"🗑️", key=f"delete_list_{list_name}"):
                        # Move contacts from deleted list to Default
                        df.loc[df['List'] == list_name, 'List'] = 'Default'
                        save_data(df)
                        # Delete the list
                        del lists_data[list_name]
                        save_lists(lists_data)
                        if st.session_state.current_list == list_name:
                            st.session_state.current_list = 'Default'
                        st.success(f"List '{list_name}' deleted and contacts moved to Default!")
                        st.rerun()

        if st.button("Done Editing"):
            st.session_state.show_edit_lists = False
            st.rerun()

    st.markdown("---")

    with st.sidebar:
        st.header("Log New Call")

        with st.form(f"contact_form_{st.session_state.form_key}", enter_to_submit=False):
            # List selection for new contact
            contact_list = st.selectbox(
                "Add to List:",
                list(lists_data.keys()),
                index=list(lists_data.keys()).index(st.session_state.current_list),
                help="Select which list to add this contact to"
            )

            business = st.text_input("Business Name")
            name = st.text_input("Contact Name")
            number = st.text_input("Phone Number")
            email = st.text_input("Email")
            location = st.text_input("Location")
            industry = st.text_input("Industry")
            call_notes = st.text_area("Call Notes")

            # JavaScript for Enter key navigation
            st.components.v1.html("""
            <script>
            function setupEnterKeyNavigation() {
                console.log('Setting up Enter key navigation...');

                // Get the parent iframe to access the main document
                let targetDocument = document;
                if (window.parent && window.parent.document) {
                    targetDocument = window.parent.document;
                }

                const inputs = Array.from(targetDocument.querySelectorAll('input[aria-label], textarea[aria-label]'));
                console.log('Found inputs:', inputs.length);

                // Filter for form inputs in the sidebar
                const formInputs = inputs.filter(input => {
                    const sidebar = input.closest('[data-testid="stSidebar"]');
                    return sidebar !== null;
                });

                console.log('Form inputs in sidebar:', formInputs.length);

                formInputs.forEach((input, index) => {
                    // Remove any existing listeners to prevent duplicates
                    input.removeEventListener('keydown', input._enterHandler);

                    input._enterHandler = function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                            console.log('Enter pressed on input', index);

                            // Check if current input is the call notes (textarea)
                            if (input.tagName.toLowerCase() === 'textarea') {
                                console.log('In call notes - submitting form');

                                // Try multiple selectors for the submit button
                                let submitBtn = targetDocument.querySelector('button[kind="secondaryFormSubmit"]');
                                if (!submitBtn) {
                                    submitBtn = targetDocument.querySelector('button[data-testid="stBaseButton-secondaryFormSubmit"]');
                                }

                                if (submitBtn) {
                                    console.log('Found submit button:', submitBtn);

                                    submitBtn.click();
                                    console.log('Clicked submit button');

                                    // Focus first input after submission and rerun
                                    setTimeout(() => {
                                        const newInputs = Array.from(targetDocument.querySelectorAll('input[aria-label], textarea[aria-label]')).filter(input => {
                                            const sidebar = input.closest('[data-testid="stSidebar"]');
                                            return sidebar !== null;
                                        });
                                        if (newInputs[0]) {
                                            newInputs[0].focus();
                                            console.log('Focused first input after submission');
                                        }
                                    }, 500);
                                } else {
                                    console.log('Submit button not found');
                                }
                            } else {
                                const nextIndex = index + 1;
                                if (nextIndex < formInputs.length) {
                                    formInputs[nextIndex].focus();
                                    console.log('Focused next input', nextIndex);
                                }
                            }
                        }
                    };

                    input.addEventListener('keydown', input._enterHandler);
                });
            }

            // Run setup with multiple attempts
            let attempts = 0;
            function trySetup() {
                attempts++;
                console.log('Setup attempt', attempts);
                setupEnterKeyNavigation();
                if (attempts < 10) {
                    setTimeout(trySetup, 500);
                }
            }

            setTimeout(trySetup, 1000);

            // Also run on DOM changes
            const observer = new MutationObserver(function(mutations) {
                setTimeout(setupEnterKeyNavigation, 200);
            });

            if (window.parent && window.parent.document) {
                observer.observe(window.parent.document.body, { childList: true, subtree: true });
            }
            </script>
            """, height=0)

            submitted = st.form_submit_button("Log Call")

            if submitted and (business or name or number or email or call_notes):
                new_contact = {
                    'Business': business or '',
                    'Name': name or '',
                    'Number': number or '',
                    'Email': email or '',
                    'Location': location or '',
                    'Industry': industry or '',
                    'Call Notes': call_notes or '',
                    'Date Added': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'List': contact_list
                }

                if df.empty:
                    df = pd.DataFrame([new_contact])
                else:
                    df = pd.concat([df, pd.DataFrame([new_contact])], ignore_index=True)

                save_data(df)
                st.session_state.form_key += 1  # Increment to create new form
                st.success("Contact added successfully!")
                st.rerun()

    st.header(f"Cold call Database - {lists_data[st.session_state.current_list]['name']}")

    if not df.empty:
        col1, col2 = st.columns([3, 1])

        with col2:
            if st.button("Clear All Data", type="secondary"):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.success("All data cleared!")
                st.rerun()

        # Filter by current list first
        list_filtered_df = df[df['List'] == st.session_state.current_list] if not df.empty else df

        search_term = st.text_input("🔍 Search contacts...", placeholder="Search by business, name, email, or industry")

        if search_term:
            mask = list_filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            filtered_df = list_filtered_df[mask]
        else:
            filtered_df = list_filtered_df

        for idx, row in filtered_df.iterrows():
            # Check if this entry is in edit mode
            edit_key = f"edit_{idx}"
            is_editing = st.session_state.get(edit_key, False)

            if is_editing:
                # Edit mode
                with st.form(f"edit_form_{idx}"):
                    st.subheader(f"Editing Contact #{idx + 1}")

                    # List selection for editing contact
                    edit_contact_list = st.selectbox("List:", list(lists_data.keys()),
                                                    index=list(lists_data.keys()).index(row.get('List', 'Default')))

                    col1, col2 = st.columns(2)
                    with col1:
                        edit_business = st.text_input("Business Name", value=row['Business'])
                        edit_name = st.text_input("Contact Name", value=row['Name'])
                        edit_number = st.text_input("Phone Number", value=row['Number'])

                    with col2:
                        edit_email = st.text_input("Email", value=row['Email'])
                        edit_location = st.text_input("Location", value=row['Location'])
                        edit_industry = st.text_input("Industry", value=row['Industry'])

                    edit_notes = st.text_area("Call Notes", value=row.get('Call Notes', ''))

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        save_changes = st.form_submit_button("💾 Save Changes")
                    with col2:
                        cancel_edit = st.form_submit_button("❌ Cancel")

                    if save_changes:
                        # Update the contact
                        df_original = load_data()
                        df_original.loc[idx, 'Business'] = edit_business
                        df_original.loc[idx, 'Name'] = edit_name
                        df_original.loc[idx, 'Number'] = edit_number
                        df_original.loc[idx, 'Email'] = edit_email
                        df_original.loc[idx, 'Location'] = edit_location
                        df_original.loc[idx, 'Industry'] = edit_industry
                        df_original.loc[idx, 'Call Notes'] = edit_notes
                        df_original.loc[idx, 'List'] = edit_contact_list

                        save_data(df_original)
                        st.session_state[edit_key] = False
                        st.success("Contact updated!")
                        st.rerun()

                    if cancel_edit:
                        st.session_state[edit_key] = False
                        st.rerun()
            else:
                # Display mode
                col1, col2 = st.columns([8, 2])

                with col1:
                    # Display list badge with color
                    contact_list = row.get('List', 'Default')
                    list_color = lists_data.get(contact_list, {}).get('color', '#1f77b4')
                    st.markdown(f'<span style="background-color:{list_color}; color:white; padding:2px 8px; border-radius:12px; font-size:12px;">{contact_list}</span>', unsafe_allow_html=True)

                    st.write(f"**#{idx + 1}** | **{row['Business']}** - {row['Name']}")
                    st.write(f"📞 {row['Number']} | ✉️ {row['Email']}")
                    st.write(f"📍 {row['Location']} | 🏢 {row['Industry']}")
                    if pd.notna(row.get('Call Notes')) and row.get('Call Notes'):
                        st.write(f"📝 **Notes:** {row['Call Notes']}")
                    st.caption(f"Added: {row['Date Added']}")

                with col2:
                    if st.button("✏️", key=f"edit_btn_{idx}", help="Edit this contact"):
                        st.session_state[edit_key] = True
                        st.rerun()

                    if st.button("🗑️", key=f"delete_{idx}", help="Delete this contact"):
                        df_original = load_data()
                        df_original = df_original.drop(df_original.index[idx]).reset_index(drop=True)
                        save_data(df_original)
                        st.success("Contact deleted!")
                        st.rerun()

            st.divider()

        st.metric("Total Contacts", len(filtered_df))

        if st.button("Download as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"contacts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No contacts yet. Add your first contact using the form in the sidebar!")

if __name__ == "__main__":
    main()