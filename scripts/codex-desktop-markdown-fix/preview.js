// Inserted inside the workspace Markdown editor's webpack module.
const markdownPreviewExtensions = [{ breaks: false }];
const WorkspaceMarkdownButton = n("pZQ9").DW;

function markdownFileDirectory(filePath) {
  const path = (0,c.tIC)(filePath) || (0,c.zjD)(filePath) ? d().win32 : d().posix;
  return path.dirname(filePath);
}

function WorkspaceMarkdownPreview({
  markdown, cwd, hostId, initialScrollTop, onScroll, onEdit, editLabel,
}) {
  const scrollPanel = h.useRef(null);
  const startAt = h.useRef(initialScrollTop);
  h.useLayoutEffect(() => {
    if (startAt.current != null) scrollPanel.current.scrollTop = startAt.current;
  }, []);

  const metadata = n("tKUf").x(markdown);
  const Renderer = n("pPxA").o;
  const children = [];
  if (onEdit) {
    children.push(i.jsx("div", {
      className: "mb-4",
      children: i.jsx(WorkspaceMarkdownButton, { onClick: onEdit, children: editLabel }),
    }, "edit"));
  }
  children.push(i.jsx(Renderer, {
    children: metadata?.body ?? markdown,
    className: "text-size-chat",
    cwd,
    hostId,
    extensions: markdownPreviewExtensions,
    externalResourcePolicy: "restricted",
    openFileLinksInSidePanel: true,
    repairOrderedLists: false,
  }, "markdown"));

  return i.jsx("div", {
    ref: scrollPanel,
    "data-workspace-markdown-preview": true,
    className: "absolute inset-0 overflow-auto px-4 pt-10 pb-8 text-start",
    onScroll: (event) => onScroll(event.currentTarget.scrollTop),
    children: i.jsx("article", {
      className: "min-w-0 w-full",
      style: { whiteSpace: "normal", overflowWrap: "anywhere" },
      children,
    }),
  });
}
