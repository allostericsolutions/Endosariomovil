Traceback:
File "/home/adminuser/venv/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 589, in _run_script
    exec(code, module.__dict__)
File "/mount/src/endosariomovil/endosos.py", line 255, in <module>
    table_html = generate_html_table(comparison_df.drop(columns=["Color"]))  # Eliminar la columna Color antes de convertir a HTML
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/mount/src/endosariomovil/endosos.py", line 249, in generate_html_table
    color = row["Color"]
            ~~~^^^^^^^^^
File "/home/adminuser/venv/lib/python3.11/site-packages/pandas/core/series.py", line 1121, in __getitem__
    return self._get_value(key)
           ^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.11/site-packages/pandas/core/series.py", line 1237, in _get_value
    loc = self.index.get_loc(label)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.11/site-packages/pandas/core/indexes/base.py", line 3812, in get_loc
    raise KeyError(key) from err

    with col2:
        download_csv = st.button("Download Comparison CSV")
        if download_csv:
            csv_buffer = create_csv(comparison_data)
            st.download_button(
                label="Download CSV",
                data=csv_buffer,
                file_name="comparison.csv",
                mime="text/csv"
            )
