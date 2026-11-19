import { useState } from 'react';
import { KeyRound, ShieldCheck, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authApi } from '../services/auth';
import { Button } from '../components/common/Button';
import { Card, InputField } from '../components/common/UI';
import { extractErrorMessage, formatDateTime } from '../utils/formatters';

export function Settings() {
  const { user, setUser } = useAuth();
  const toast = useToast();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileError, setProfileError] = useState('');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (fullName.trim().length < 2) {
      setProfileError('Full name must be at least 2 characters.');
      return;
    }
    setProfileBusy(true);
    setProfileError('');
    try {
      const updated = await authApi.updateMe({ full_name: fullName.trim() });
      setUser(updated);
      toast.success('Profile updated successfully.');
    } catch (err) {
      setProfileError(extractErrorMessage(err, 'Unable to update profile.'));
    } finally {
      setProfileBusy(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError('');
    if (newPassword.length < 8 || !/[a-zA-Z]/.test(newPassword) || !/\d/.test(newPassword)) {
      setPasswordError('New password must be at least 8 characters and contain letters and numbers.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }
    setPasswordBusy(true);
    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast.success('Password changed successfully.');
    } catch (err) {
      setPasswordError(extractErrorMessage(err, 'Unable to change password.'));
    } finally {
      setPasswordBusy(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[#101010]">Account Settings</h2>
        <p className="text-sm text-[#737373]">
          Manage your SprintFlow profile details and account security.
        </p>
      </div>

      {/* Profile Settings */}
      <Card className="p-6">
        <div className="flex items-center gap-2.5 mb-5">
          <div className="w-9 h-9 rounded-lg bg-[#101010] text-[#75C900] flex items-center justify-center">
            <User className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#101010]">Profile Information</h3>
            <p className="text-xs text-[#737373]">Update how your name appears to your team</p>
          </div>
        </div>

        <form onSubmit={handleSaveProfile} className="space-y-4">
          {profileError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3.5 py-2.5 text-xs text-[#DC2626]">
              {profileError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InputField
              label="Full Name"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            <InputField
              label="Email Address"
              value={user?.email || ''}
              disabled
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-[#737373]">
              Member since {formatDateTime(user?.created_at)}
            </span>
            <Button type="submit" loading={profileBusy}>
              Save Profile
            </Button>
          </div>
        </form>
      </Card>

      {/* Password Settings */}
      <Card className="p-6">
        <div className="flex items-center gap-2.5 mb-5">
          <div className="w-9 h-9 rounded-lg bg-[#101010] text-[#75C900] flex items-center justify-center">
            <KeyRound className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#101010]">Change Password</h3>
            <p className="text-xs text-[#737373]">
              Passwords are salted and hashed with bcrypt before storage
            </p>
          </div>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4">
          {passwordError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3.5 py-2.5 text-xs text-[#DC2626]">
              {passwordError}
            </div>
          )}

          <InputField
            label="Current Password"
            type="password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InputField
              label="New Password"
              type="password"
              required
              placeholder="Min 8 chars, letters + numbers"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <InputField
              label="Confirm New Password"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          <div className="flex justify-end pt-2">
            <Button type="submit" loading={passwordBusy}>
              Update Password
            </Button>
          </div>
        </form>
      </Card>

      {/* Security overview */}
      <Card surface className="p-5 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-[#16A34A] shrink-0 mt-0.5" />
        <div className="text-xs text-[#737373] space-y-1">
          <p className="font-semibold text-[#101010]">Active Session & Security Controls</p>
          <p>
            Authenticated via signed JWT Bearer token. Project access, user stories, tasks,
            activity logs, and notifications are strictly authorized server-side per project membership and user ownership.
          </p>
        </div>
      </Card>
    </div>
  );
}
