import React, { useState } from 'react';
import { Modal, Box, Text, Button, Input, IconButton } from '@sema4ai/components';
import { Plus, Trash } from 'lucide-react';

interface RobotRunInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (inputs: Record<string, string>) => void;
  robotName: string;
  taskName: string;
}

export const RobotRunInputModal: React.FC<RobotRunInputModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  robotName,
  taskName,
}) => {
  const [inputs, setInputs] = useState<Array<{ key: string; value: string }>>([
    { key: '', value: '' },
  ]);
  const [submitting, setSubmitting] = useState(false);

  const handleInputChange = (idx: number, field: 'key' | 'value', value: string) => {
    setInputs((prev) => {
      const next = [...prev];
      next[idx][field] = value;
      return next;
    });
  };

  const handleAddField = () => {
    setInputs((prev) => [...prev, { key: '', value: '' }]);
  };

  const handleRemoveField = (idx: number) => {
    setInputs((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = () => {
    setSubmitting(true);
    const inputObj: Record<string, string> = {};
    for (const { key, value } of inputs) {
      if (key) inputObj[key] = value;
    }
    onSubmit(inputObj);
    setSubmitting(false);
    onClose();
  };

  return (
    <Modal open={isOpen} onClose={onClose} title={`Run Task: ${robotName} / ${taskName}`}> 
      <Box mb={16}>
        <Text mb={8}>Provide input values for the task (optional):</Text>
        {inputs.map((input, idx) => (
          <Box key={idx} display="flex" alignItems="center" mb={8}>
            <Input
              placeholder="Key"
              value={input.key}
              onChange={(e) => handleInputChange(idx, 'key', e.target.value)}
              style={{ marginRight: 8 }}
            />
            <Input
              placeholder="Value"
              value={input.value}
              onChange={(e) => handleInputChange(idx, 'value', e.target.value)}
              style={{ marginRight: 8 }}
            />
            <IconButton
              aria-label="Remove"
              onClick={() => handleRemoveField(idx)}
              disabled={inputs.length === 1}
              size="sm"
            >
              <Trash size={16} />
            </IconButton>
          </Box>
        ))}
        <Button variant="ghost" size="xs" onClick={handleAddField} leftIcon={<Plus size={16} />}>Add Input</Button>
      </Box>
      <Box display="flex" justifyContent="flex-end">
        <Button variant="secondary" onClick={onClose} style={{ marginRight: 8 }}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit} loading={submitting}>
          Run Task
        </Button>
      </Box>
    </Modal>
  );
};
