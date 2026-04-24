/** 将后端返回的扁平菜单转为树（用于侧栏分组，如「系统管理」）。 */

export interface MenuFlat {
  id: number
  parent_id: number
  name: string
  path: string | null
  icon: string | null
  permission: string | null
  sort: number
}

export interface MenuNode extends MenuFlat {
  children?: MenuNode[]
}

export function buildMenuTree(flat: MenuFlat[]): MenuNode[] {
  if (!flat.length) return []
  const map = new Map<number, MenuNode & { children: MenuNode[] }>()
  for (const m of flat) {
    map.set(m.id, { ...m, children: [] })
  }
  const roots: (MenuNode & { children: MenuNode[] })[] = []
  for (const m of flat) {
    const node = map.get(m.id)!
    if (!m.parent_id) {
      roots.push(node)
    } else {
      const p = map.get(m.parent_id)
      if (p) p.children.push(node)
      else roots.push(node)
    }
  }
  const sortRec = (nodes: MenuNode[]) => {
    nodes.sort((a, b) => a.sort - b.sort)
    for (const n of nodes) {
      if (n.children?.length) sortRec(n.children)
    }
  }
  sortRec(roots)
  return roots
}
