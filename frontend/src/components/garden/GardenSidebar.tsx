import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Folder,
  FolderOpen,
  FileText,
  ChevronRight,
  ChevronDown,
  Search,
  ListTree,
  Hash,
  Sparkles,
} from "lucide-react";
import { api, ContentTreeItem, HeadingItem } from "../../services/api";

interface GardenSidebarProps {
  currentPath: string;
  onSelectNote: (path: string) => void;
  headings?: HeadingItem[];
  isOpen: boolean;
  onClose?: () => void;
}

export const GardenSidebar: React.FC<GardenSidebarProps> = ({
  currentPath,
  onSelectNote,
  headings = [],
  isOpen,
  onClose,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    "plans": true,
    "plans/week-01": true,
  });
  const [activeTab, setActiveTab] = useState<"tree" | "toc">("tree");

  const { data: tree = [], isLoading } = useQuery({
    queryKey: ["content", "tree"],
    queryFn: () => api.getContentTree(),
    staleTime: 1000 * 60 * 5,
  });

  const toggleFolder = (folderId: string) => {
    setExpandedFolders((prev) => ({
      ...prev,
      [folderId]: !prev[folderId],
    }));
  };

  const normalizePath = (p: string) => p.replace(/\\/g, "/").replace(/^\/+|\/+$/g, "");

  // Tự động mở rộng các thư mục cha chứa note đang được chọn (khi mở trực tiếp qua URL hoặc reload F5)
  useEffect(() => {
    if (!tree.length || !currentPath) return;
    const normCurrent = normalizePath(currentPath);
    const expandMatchingParents = (nodes: ContentTreeItem[]): boolean => {
      let foundInBranch = false;
      for (const node of nodes) {
        if (normalizePath(node.path) === normCurrent) {
          foundInBranch = true;
        }
        if (node.children && expandMatchingParents(node.children)) {
          setExpandedFolders((prev) => ({ ...prev, [node.id]: true }));
          foundInBranch = true;
        }
      }
      return foundInBranch;
    };
    expandMatchingParents(tree);
  }, [tree, currentPath]);

  // Recursive tree rendering
  const renderTreeItem = (item: ContentTreeItem, depth = 0) => {
    const isFolder = item.type === "folder";
    const isExpanded = expandedFolders[item.id] ?? depth === 0;
    const isSelected = normalizePath(currentPath) === normalizePath(item.path);

    // Filter check
    if (searchTerm) {
      const matchSelf = item.title.toLowerCase().includes(searchTerm.toLowerCase());
      const hasMatchingChild = (children: ContentTreeItem[]): boolean =>
        children.some(
          (c) =>
            c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            hasMatchingChild(c.children || []),
        );
      if (!matchSelf && (!item.children || !hasMatchingChild(item.children))) {
        return null;
      }
    }

    if (isFolder) {
      const hasNote = item.path && item.path.endsWith(".md");
      const isSelected = hasNote && normalizePath(currentPath) === normalizePath(item.path);

      return (
        <div key={item.id} className="select-none">
          <div
            style={{ paddingLeft: `${depth * 10 + 4}px` }}
            className={`w-full flex items-center gap-1 py-1 pr-1.5 rounded-lg text-xs font-semibold transition group ${
              isSelected
                ? "bg-apple-blue text-white shadow-sm font-bold"
                : "text-gray-700 dark:text-gray-200 hover:bg-gray-100/80 dark:hover:bg-gray-800/60"
            }`}
          >
            {/* Nút Chevron toggle mở/đóng */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                toggleFolder(item.id);
              }}
              className={`p-1 rounded transition ${
                isSelected
                  ? "text-white/80 hover:text-white hover:bg-white/20"
                  : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-200/60 dark:hover:bg-gray-700/60"
              }`}
              title={isExpanded ? "Thu gọn thư mục" : "Mở rộng thư mục"}
            >
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 flex-shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" />
              )}
            </button>

            {/* Bấm vào Folder Icon + Tên để MỞ KẾ HOẠCH TUẦN */}
            <button
              type="button"
              onClick={() => {
                if (hasNote) {
                  onSelectNote(item.path);
                  if (!isExpanded) {
                    setExpandedFolders((prev) => ({ ...prev, [item.id]: true }));
                  }
                  if (window.innerWidth < 1024 && onClose) {
                    onClose();
                  }
                } else {
                  toggleFolder(item.id);
                }
              }}
              className="flex-1 flex items-center gap-1.5 py-0.5 text-left truncate cursor-pointer"
              title={hasNote ? `Xem tài liệu: ${item.title}` : item.title}
            >
              {isExpanded ? (
                <FolderOpen className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? "text-white" : "text-apple-blue"}`} />
              ) : (
                <Folder className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? "text-white" : "text-apple-blue"}`} />
              )}
              <span className="truncate">{item.title}</span>
            </button>
          </div>

          {isExpanded && item.children && (
            <div className="space-y-0.5 mt-0.5">
              {item.children.map((child) => renderTreeItem(child, depth + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <button
        key={item.id}
        type="button"
        onClick={() => {
          onSelectNote(item.path);
          if (window.innerWidth < 1024 && onClose) {
            onClose();
          }
        }}
        style={{ paddingLeft: `${depth * 12 + 12}px` }}
        className={`w-full flex items-center gap-2 py-1.5 pr-2 rounded-lg text-xs font-medium transition text-left ${
          isSelected
            ? "bg-apple-blue text-white font-semibold shadow-sm"
            : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/60 hover:text-gray-900 dark:hover:text-gray-100"
        }`}
      >
        <FileText
          className={`w-3.5 h-3.5 flex-shrink-0 ${
            isSelected ? "text-white" : "text-gray-400"
          }`}
        />
        <span className="truncate">{item.title}</span>
      </button>
    );
  };

  const handleHeadingClick = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (window.innerWidth < 1024 && onClose) {
      onClose();
    }
  };

  return (
    <aside
      className={`fixed lg:sticky lg:top-20 inset-y-0 left-0 z-30 w-72 flex-shrink-0 bg-white/95 dark:bg-[#16181f]/95 backdrop-blur-md border-r border-gray-200 dark:border-gray-800 flex flex-col transition-transform duration-200 self-start max-h-[calc(100vh-6rem)] ${
        isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      }`}
    >
      {/* Top Header & Tabs */}
      <div className="p-3 border-b border-gray-100 dark:border-gray-800 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-bold text-gray-900 dark:text-gray-100">
            <Sparkles className="w-4 h-4 text-apple-blue" />
            <span>Digital Garden Explorer</span>
          </div>

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="lg:hidden p-1 text-gray-400 hover:text-gray-600 text-xs font-bold"
            >
              ✕
            </button>
          )}
        </div>

        {/* Tab switcher: Tree vs TOC */}
        <div className="grid grid-cols-2 gap-1 p-0.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab("tree")}
            className={`py-1 rounded-md flex items-center justify-center gap-1 transition ${
              activeTab === "tree"
                ? "bg-white dark:bg-gray-700 text-apple-blue shadow-sm"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            <ListTree className="w-3 h-3" />
            <span>Tài Liệu</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("toc")}
            className={`py-1 rounded-md flex items-center justify-center gap-1 transition ${
              activeTab === "toc"
                ? "bg-white dark:bg-gray-700 text-apple-blue shadow-sm"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            <Hash className="w-3 h-3" />
            <span>Mục Lục ({headings.length})</span>
          </button>
        </div>

        {/* Search input for tree */}
        {activeTab === "tree" && (
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Tìm nhanh bài ghi chú..."
              className="w-full pl-8 pr-2.5 py-1.5 bg-gray-50 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-lg text-xs placeholder-gray-400 focus:outline-none focus:border-apple-blue"
            />
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto no-scrollbar scrollbar-none p-2 space-y-1">
        {activeTab === "tree" ? (
          isLoading ? (
            <div className="p-4 text-center text-xs text-gray-400">
              Đang tải danh mục...
            </div>
          ) : tree.length === 0 ? (
            <div className="p-4 text-center text-xs text-gray-400">
              Không có tài liệu nào.
            </div>
          ) : (
            tree.map((item) => renderTreeItem(item, 0))
          )
        ) : headings.length === 0 ? (
          <div className="p-4 text-center text-xs text-gray-400">
            Bài này không có tiêu đề mục lục.
          </div>
        ) : (
          <div className="space-y-1">
            {headings.map((h, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleHeadingClick(h.id)}
                style={{ paddingLeft: `${(h.level - 1) * 12 + 8}px` }}
                className="w-full text-left py-1 pr-2 text-xs text-gray-600 dark:text-gray-400 hover:text-apple-blue hover:bg-gray-50 dark:hover:bg-gray-800/60 rounded-lg transition truncate block"
              >
                {h.text}
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
};
