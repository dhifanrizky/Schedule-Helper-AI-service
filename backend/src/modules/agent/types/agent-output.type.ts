export type RawTask = {
  task_id: string;
  title: string;
  description: string;
  raw_time: string;
  raw_input: string;
  category: string;
};

export type RouterType = {
  current_intent: string;
  raw_tasks: RawTask[];
};
