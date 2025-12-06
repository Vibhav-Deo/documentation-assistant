'use client'

import { useCallback, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import type { TicketRelationship } from '@/types'

interface RelationshipGraphProps {
  data: TicketRelationship
  ticketKey: string
}

export default function RelationshipGraph({ data, ticketKey }: RelationshipGraphProps) {
  // Create nodes and edges from the relationship data
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = []
    const edges: Edge[] = []

    // Central ticket node
    nodes.push({
      id: 'ticket',
      type: 'default',
      data: { label: `🎫 ${ticketKey}` },
      position: { x: 400, y: 200 },
      style: {
        background: '#4f46e5',
        color: 'white',
        border: '2px solid #4338ca',
        borderRadius: '8px',
        padding: '10px',
        fontWeight: 'bold',
      },
    })

    // Add commit nodes
    data.commits?.forEach((commit, idx) => {
      const nodeId = `commit-${idx}`
      nodes.push({
        id: nodeId,
        data: { label: `💾 ${commit.message.substring(0, 30)}...` },
        position: { x: 100, y: 50 + idx * 80 },
        style: {
          background: '#a855f7',
          color: 'white',
          borderRadius: '6px',
          fontSize: '12px',
          padding: '8px',
        },
      })
      edges.push({
        id: `ticket-${nodeId}`,
        source: 'ticket',
        target: nodeId,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
      })
    })

    // Add PR nodes
    data.pull_requests?.forEach((pr, idx) => {
      const nodeId = `pr-${idx}`
      nodes.push({
        id: nodeId,
        data: { label: `🔀 PR #${pr.pr_number}` },
        position: { x: 700, y: 50 + idx * 80 },
        style: {
          background: '#22c55e',
          color: 'white',
          borderRadius: '6px',
          fontSize: '12px',
          padding: '8px',
        },
      })
      edges.push({
        id: `ticket-${nodeId}`,
        source: 'ticket',
        target: nodeId,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
      })
    })

    // Add developer nodes
    data.developers?.forEach((dev, idx) => {
      const nodeId = `dev-${idx}`
      nodes.push({
        id: nodeId,
        data: { label: `👨‍💻 ${dev.name}` },
        position: { x: 250 + idx * 150, y: 400 },
        style: {
          background: '#3b82f6',
          color: 'white',
          borderRadius: '6px',
          fontSize: '12px',
          padding: '8px',
        },
      })
      edges.push({
        id: `ticket-${nodeId}`,
        source: 'ticket',
        target: nodeId,
        markerEnd: { type: MarkerType.ArrowClosed },
      })
    })

    // Add file nodes (limit to first 5 for readability)
    data.code_files?.slice(0, 5).forEach((file, idx) => {
      const nodeId = `file-${idx}`
      const fileName = file.file_path.split('/').pop() || file.file_path
      nodes.push({
        id: nodeId,
        data: { label: `📝 ${fileName}` },
        position: { x: 200 + idx * 120, y: 550 },
        style: {
          background: '#f97316',
          color: 'white',
          borderRadius: '6px',
          fontSize: '11px',
          padding: '6px',
        },
      })
      edges.push({
        id: `ticket-${nodeId}`,
        source: 'ticket',
        target: nodeId,
        style: { strokeDasharray: '5 5' },
      })
    })

    return { initialNodes: nodes, initialEdges: edges }
  }, [data, ticketKey])

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  return (
    <div style={{ height: '600px' }} className="border border-gray-200 rounded-lg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  )
}
