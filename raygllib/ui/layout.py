from .base import LayoutDirection
from raygllib import utils

HORIZONTAL = LayoutDirection.HORIZONTAL
VERTICAL = LayoutDirection.VERTICAL


def _dump_widget_tree(widget, extra, indent=0):
    if indent == 0:
        print('-' * 80)
    print(' ' * indent, widget, extra(widget))
    for child in widget.children:
        _dump_widget_tree(child, extra, indent + 4)


def preorder_traversal(widget):
    yield widget
    for child in widget.children:
        child.parent = widget
        yield from preorder_traversal(child)


class LayoutManager:
    def __init__(self, rootWidget):
        self.root = rootWidget
        self.widgets = []

    def relayout(self):
        widgets = self.widgets = list(preorder_traversal(self.root))
        nWidgets = len(widgets)
        fixedW = [0] * nWidgets
        fixedH = [0] * nWidgets
        varyW = [0] * nWidgets
        varyH = [0] * nWidgets
        idMap = {widget: i for i, widget in enumerate(widgets)}

        def extra_info(widget):
            i = idMap[widget]
            return 'fw:{} vw:{} fh:{} vh:{}'.format(
                fixedW[i], varyW[i], fixedH[i], varyH[i])

        def set_size(i, total, fixed, vary, matchDir, attr):
            widget = widgets[i]
            dir = widget.layoutDirection
            if dir != matchDir:
                for child in widget.children:
                    # Say, if we are setting width, then dir == VERTICAL now.
                    j = idMap[child]
                    set_size(j, total, fixed, vary, matchDir, attr)
            else:
                # Say, if we are setting width, then dir == HORIZONTAL now.
                if vary[i] <= 1e-8:
                    pass
                totalFixed = 0
                totalVary = 0
                for child in widget.children:
                    j = idMap[child]
                    totalFixed += fixed[j]
                    totalVary += vary[j]
                vary1 = (total - totalFixed) / totalVary if totalVary > 0 else 0
                for child in widget.children:
                    j = idMap[child]
                    set_size(j, fixed[j] + vary1 * vary[j], fixed, vary, matchDir, attr)

            setattr(widget, attr, total)

        def set_fixed_vary(i, fixed, vary, matchDir, attr):
            widget = widgets[i]
            for child in widget.children:
                set_fixed_vary(idMap[child], fixed, vary, matchDir, attr)
            dir = widget.layoutDirection
            if widget.parent and widget.parent.layoutDirection == matchDir\
                    and widget.fixedSize:
                fixed[i] = getattr(widget, attr)
            elif not widget.children:
                vary[i] = 1
            else:
                if dir != matchDir:
                    # Say, if we are setting width, then dir == VERTICAL now.
                    for child in widget.children:
                        j = idMap[child]
                        fixed[i] = max(fixed[i], fixed[j])
                        vary[i] = max(vary[i], vary[j])
                else:
                    # Say, if we are setting width, then dir == HORIZONTAL now.
                    for child in widget.children:
                        j = idMap[child]
                        fixed[i] += fixed[j]
                        vary[i] += vary[j]

        # _dump_widget_tree(widgets[0], extra_info)

        set_fixed_vary(0, fixedW, varyW, HORIZONTAL, 'width')
        set_fixed_vary(0, fixedH, varyH, VERTICAL, 'height')
        set_size(0, widgets[0].width, fixedW, varyW, HORIZONTAL, 'width')
        set_size(0, widgets[0].height, fixedH, varyH, VERTICAL, 'height')

        # _dump_widget_tree(widgets[0], extra_info)

        for widget in widgets:
            posX, posY = widget.x, widget.y
            if widget.layoutDirection == LayoutDirection.HORIZONTAL:
                for child in widget.children:
                    child.x = posX
                    child.y = posY
                    posX += child.width
            elif widget.layoutDirection == LayoutDirection.VERTICAL:
                for child in widget.children:
                    child.x = posX
                    child.y = posY
                    posY += child.height

        for widget in widgets:
            widget.on_relayout()

        # _dump_widget_tree(widgets[0], extra_info)
        # print('nWidgets', nWidgets)
