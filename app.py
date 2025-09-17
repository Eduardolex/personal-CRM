import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Personal CRM", page_icon="📊", layout="wide")

DATA_FILE = "contacts_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    return pd.DataFrame(columns=['Business', 'Name', 'Number', 'Email', 'Location', 'Industry', 'Call Notes', 'Date Added'])

def save_data(df):
    data = df.to_dict('records')
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    st.title("📊 Personal CRM")
    st.markdown("---")

    # Initialize session state for form key
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0

    df = load_data()

    with st.sidebar:
        st.header("Log New Call")

        with st.form(f"contact_form_{st.session_state.form_key}", enter_to_submit=False):
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

            if submitted and business and name:
                new_contact = {
                    'Business': business,
                    'Name': name,
                    'Number': number,
                    'Email': email,
                    'Location': location,
                    'Industry': industry,
                    'Call Notes': call_notes,
                    'Date Added': datetime.now().strftime("%Y-%m-%d %H:%M")
                }

                if df.empty:
                    df = pd.DataFrame([new_contact])
                else:
                    df = pd.concat([df, pd.DataFrame([new_contact])], ignore_index=True)

                save_data(df)
                st.session_state.form_key += 1  # Increment to create new form
                st.success("Contact added successfully!")
                st.rerun()

    st.header("Cold call Database")

    if not df.empty:
        col1, col2 = st.columns([3, 1])

        with col2:
            if st.button("Clear All Data", type="secondary"):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.success("All data cleared!")
                st.rerun()

        search_term = st.text_input("🔍 Search contacts...", placeholder="Search by business, name, email, or industry")

        if search_term:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            filtered_df = df[mask]
        else:
            filtered_df = df

        for idx, row in filtered_df.iterrows():
            # Check if this entry is in edit mode
            edit_key = f"edit_{idx}"
            is_editing = st.session_state.get(edit_key, False)

            if is_editing:
                # Edit mode
                with st.form(f"edit_form_{idx}"):
                    st.subheader(f"Editing Contact #{idx + 1}")

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