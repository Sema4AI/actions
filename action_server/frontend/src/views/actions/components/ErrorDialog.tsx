import { Button, Dialog } from '@robocorp/components';
import { FC } from 'react';

export interface ErrorDialogInfo {
  errorTitle: string;
  errorMessage: string;
}

export const ErrorDialog: FC<{ info: ErrorDialogInfo; clearError: any }> = ({
  info,
  clearError,
}) => {
  return (
    <Dialog
      open={true}
      onClose={() => {
        clearError();
      }}
      size="medium"
    >
      <Dialog.Header>
        <Dialog.Header.Description>{info.errorTitle}</Dialog.Header.Description>
      </Dialog.Header>
      <Dialog.Content>{info.errorMessage}</Dialog.Content>
      <Dialog.Actions>
        <Button
          onClick={() => {
            clearError();
          }}
          variant="primary"
        >
          Close
        </Button>
      </Dialog.Actions>
    </Dialog>
  );
};
