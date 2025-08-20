"use client"

import React, { createContext, forwardRef, useCallback, useContext, useEffect, useState } from "react"
import { ChevronRight, File, Folder as FolderIcon, FolderOpen } from "lucide-react"
import { cn } from "@/lib/utils"

const TreeContext = createContext<{
  selectedId?: string
  expandedItems?: string[]
  indicator?: boolean
  handleExpand?: (id: string) => void
  handleSelect?: (id: string) => void
  dir?: "rtl" | "ltr"
  direction?: "rtl" | "ltr"
} | null>(null)

const useTree = () => {
  const context = useContext(TreeContext)
  if (!context) {
    throw new Error("useTree must be used within a TreeProvider")
  }
  return context
}

interface TreeViewElement {
  id: string
  name: string
  isSelectable?: boolean
  children?: TreeViewElement[]
}

type TreeProps = React.HTMLAttributes<HTMLDivElement> & {
  initialSelectedId?: string
  indicator?: boolean
  elements?: TreeViewElement[]
  initialExpandedItems?: string[]
  openIcon?: React.ReactNode
  closeIcon?: React.ReactNode
  dir?: "rtl" | "ltr"
}

const Tree = forwardRef<HTMLDivElement, TreeProps>(
  (
    {
      className,
      elements,
      initialSelectedId,
      initialExpandedItems,
      children,
      indicator = true,
      openIcon,
      closeIcon,
      dir = "ltr",
      ...props
    },
    ref,
  ) => {
    const [selectedId, setSelectedId] = useState<string | undefined>(initialSelectedId)
    const [expandedItems, setExpandedItems] = useState<string[]>(initialExpandedItems || [])

    const handleExpand = useCallback((id: string) => {
      setExpandedItems((prev) => {
        if (prev.includes(id)) {
          return prev.filter((item) => item !== id)
        }
        return [...prev, id]
      })
    }, [])

    const handleSelect = useCallback((id: string) => {
      setSelectedId(id)
    }, [])

    const expandSpecificTargetedElements = useCallback(
      (elements?: TreeViewElement[], selectId?: string) => {
        if (!elements || !selectId) return
        const findParent = (
          currentElement: TreeViewElement,
          currentPath: string[] = [],
        ): string[] | null => {
          const isSelectable = currentElement.isSelectable ?? true
          const newPath = [...currentPath, currentElement.id]
          if (currentElement.id === selectId) {
            if (isSelectable) {
              setExpandedItems((prev) => [...prev, ...newPath])
            }
            return newPath
          }
          if (isSelectable && currentElement.children && currentElement.children.length > 0) {
            const result = currentElement.children
              .map((child) => findParent(child, newPath))
              .find((path) => path !== null)
            return result ?? null
          }
          return null
        }

        elements.forEach((element) => findParent(element))
      },
      [],
    )

    useEffect(() => {
      if (initialSelectedId) {
        expandSpecificTargetedElements(elements, initialSelectedId)
      }
    }, [initialSelectedId, elements])

    const direction = dir === "rtl" ? "rtl" : "ltr"

    return (
      <TreeContext.Provider
        value={{
          selectedId,
          expandedItems,
          handleExpand,
          handleSelect,
          indicator,
          dir: direction,
          direction,
        }}
      >
        <div className={cn("size-full", className)}>
          <div ref={ref} className="relative overflow-hidden" {...props}>
            <div
              className="relative flex flex-col gap-1 overflow-y-auto"
              dir={direction}
            >
              {children}
            </div>
          </div>
        </div>
      </TreeContext.Provider>
    )
  },
)

Tree.displayName = "Tree"

const TreeIndicator = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  const { indicator, dir } = useTree()

  return (
    <>
      {indicator && (
        <div
          ref={ref}
          className={cn(
            "absolute left-1.5 w-px bg-muted-foreground/20 duration-300 ease-in-out hover:bg-slate-300 py-3",
            dir === "rtl" ? "right-1.5" : "left-1.5",
            className,
          )}
          {...props}
        />
      )}
    </>
  )
})

TreeIndicator.displayName = "TreeIndicator"

interface FolderComponentProps extends React.ComponentPropsWithoutRef<"div"> {
  expandedItems?: string[]
  element: string
  isSelectable?: boolean
  isSelect?: boolean
  value: string
}

const Folder = forwardRef<
  HTMLDivElement,
  FolderComponentProps & {
    expandedItems?: string[]
    element: string
    value: string
    isSelectable?: boolean
    isSelect?: boolean
  }
>(
  (
    {
      className,
      element,
      value,
      isSelectable = true,
      isSelect,
      children,
      ...props
    },
    ref,
  ) => {
    const {
      direction,
      handleExpand,
      expandedItems,
      indicator,
      handleSelect,
      selectedId,
    } = useTree()

    return (
      <div
        ref={ref}
        className={cn("relative flex flex-col", className)}
        {...props}
      >
        <div
          className={cn(
            `flex items-center gap-2 cursor-pointer px-2 py-2 before:absolute before:left-0 before:w-full before:opacity-0 before:bg-muted/80 before:h-[1.75rem] before:-z-10`,
            selectedId === value && "before:opacity-100",
            isSelectable ? "cursor-pointer" : "cursor-not-allowed opacity-50",
          )}
          onClick={() => {
            if (isSelectable) {
              handleExpand?.(value)
              handleSelect?.(value)
            }
          }}
        >
          {expandedItems?.includes(value) ? (
            <FolderOpen className="size-4 text-accent-foreground" />
          ) : (
            <FolderIcon className="size-4 text-accent-foreground" />
          )}

          <span className="text-sm truncate">{element}</span>
        </div>
        <div
          className={cn(
            "ml-5 flex flex-col items-start gap-1 transition-all duration-300 ease-in-out",
            expandedItems?.includes(value)
              ? "max-h-screen opacity-100"
              : "max-h-0 opacity-0",
          )}
        >
          <TreeIndicator aria-hidden="true" />
          {children}
        </div>
      </div>
    )
  },
)

Folder.displayName = "Folder"

const FileComponent = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    value: string
    handleSelect?: (id: string) => void
    isSelectable?: boolean
    isSelect?: boolean
    fileIcon?: React.ReactNode
  }
>(
  (
    {
      value,
      className,
      handleSelect,
      isSelectable = true,
      isSelect,
      fileIcon,
      children,
      ...props
    },
    ref,
  ) => {
    const { selectedId, handleSelect: treeHandleSelect } = useTree()
    const isSelected = isSelect ?? selectedId === value

    return (
      <div
        ref={ref}
        className={cn(
          "flex items-center gap-2 cursor-pointer px-2 py-2 before:absolute before:left-0 before:w-full before:opacity-0 before:bg-muted/80 before:h-[1.75rem] before:-z-10",
          isSelected && "before:opacity-100",
          isSelectable ? "cursor-pointer" : "cursor-not-allowed opacity-50",
          className,
        )}
        onClick={() => {
          if (isSelectable) {
            handleSelect?.(value)
            treeHandleSelect?.(value)
          }
        }}
        {...props}
      >
        {fileIcon ?? <File className="size-4 text-accent-foreground" />}
        <span className="text-sm truncate flex-1">{children}</span>
      </div>
    )
  },
)

FileComponent.displayName = "File"

const CollapseButton = forwardRef<
  HTMLButtonElement,
  {
    elements: TreeViewElement[]
    expandAll?: boolean
  } & React.HTMLAttributes<HTMLButtonElement>
>(({ className, elements, expandAll = false, children, ...props }, ref) => {
  const { expandedItems, handleExpand } = useTree()

  const expendAllTree = useCallback((elements: TreeViewElement[]) => {
    const expandTree = (element: TreeViewElement) => {
      handleExpand?.(element.id)
      if (element.children && element.children.length > 0) {
        element.children.forEach(expandTree)
      }
    }

    elements.forEach(expandTree)
  }, [handleExpand])

  return (
    <button
      ref={ref}
      className={cn("", className)}
      onClick={() => expendAllTree(elements)}
      {...props}
    >
      {children}
    </button>
  )
})

CollapseButton.displayName = "CollapseButton"

export { Tree, Folder, FileComponent as File, CollapseButton, type TreeViewElement }
