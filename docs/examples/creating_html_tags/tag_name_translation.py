from reactpy import html

# start
# Underscores become dashes, and a trailing underscore is stripped -- the name
# is translated, not looked up.
print(html.del_("removed")["tagName"])  # del
print(html.data_table()["tagName"])  # data-table
print(html.my_widget()["tagName"])  # my-widget

# The same constructor comes back every time, so identity checks are cheap.
print(html.my_widget is html.my_widget)  # True
# end
