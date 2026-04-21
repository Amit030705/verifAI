"use client";

import { Bell, Mail, ShieldCheck, UserCog } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function TpoSettingsPage() {
  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full pb-10">
      <div className="mx-auto w-full max-w-7xl space-y-8">
        <section className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
          <p className="text-sm text-slate-600">Manage dashboard preferences, communication defaults, and access controls.</p>
        </section>

        <section className="grid gap-4 md:grid-cols-4">
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Profile</CardTitle>
              <UserCog className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">TPO account defaults</CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Mail</CardTitle>
              <Mail className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">Email sender defaults</CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Notifications</CardTitle>
              <Bell className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">Alerts and reminders</CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Access</CardTitle>
              <ShieldCheck className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">Security and permissions</CardContent>
          </Card>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">TPO Profile Defaults</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <Input placeholder="Display name" className="h-10 rounded-xl border-slate-200" />
              <Input placeholder="Official TPO email" className="h-10 rounded-xl border-slate-200" />
              <Input placeholder="Contact number" className="h-10 rounded-xl border-slate-200" />
              <Input placeholder="Institute name" className="h-10 rounded-xl border-slate-200" />
            </CardContent>
          </Card>

          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Mail Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <Input placeholder="Sender name (e.g., TPO Cell)" className="h-10 rounded-xl border-slate-200" />
              <Input placeholder="Reply-to email" className="h-10 rounded-xl border-slate-200" />
              <Input placeholder="Default interview timezone (e.g., Asia/Kolkata)" className="h-10 rounded-xl border-slate-200" />
              <div className="rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-xs text-slate-600">
                Gmail SMTP/app-password and provider credentials are managed via backend environment configuration.
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-5">
              <label className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-sm text-slate-700">
                Group stale reminder (7+ days)
                <input type="checkbox" defaultChecked className="size-4 accent-blue-600" />
              </label>
              <label className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-sm text-slate-700">
                Daily queue summary
                <input type="checkbox" defaultChecked className="size-4 accent-blue-600" />
              </label>
              <label className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-sm text-slate-700">
                Placement update confirmations
                <input type="checkbox" defaultChecked className="size-4 accent-blue-600" />
              </label>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Access & Security</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <Input placeholder="Current password" type="password" className="h-10 rounded-xl border-slate-200" />
              <Input placeholder="New password" type="password" className="h-10 rounded-xl border-slate-200" />
              <Input placeholder="Confirm new password" type="password" className="h-10 rounded-xl border-slate-200" />
              <div className="rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-xs text-slate-600">
                API key fallback and token policy are enforced server-side for TPO endpoints.
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="flex items-center justify-end gap-2">
          <Button variant="outline" className="h-9 rounded-full px-4 border-slate-200 text-slate-700 hover:bg-slate-50">
            Reset
          </Button>
          <Button className="h-9 rounded-full px-5 bg-blue-600 hover:bg-blue-700 text-white">
            Save Settings
          </Button>
        </section>
      </div>
    </div>
  );
}
